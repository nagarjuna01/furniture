# modular_config/views.py

from rest_framework import viewsets, mixins, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import DecimalField
from django.db.models.functions import Cast
from django.db.models import Q
from rest_framework.filters import OrderingFilter  # <-- NEW
from django_filters.rest_framework import DjangoFilterBackend # <-- NEW
from django.db.models import F # <-- NEW IMPORT
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from accounts.mixins import TenantSafeViewSetMixin
from .serializers import (
    ModularProductSerializer, 
    WoodEnMiniSerializer, HardwareMiniSerializer,
    EdgeBandMiniSerializer, ModularProductCategorySerializer,ModularProductModelSerializer, ModularProductTypeSerializer
)
from .models import ModularProduct,ModularProductCategory,ModularProductModel, ModularProductType
from material.models.wood import WoodMaterial
from material.models.edgeband import EdgeBand
from material.models.hardware import Hardware
from rest_framework.permissions import IsAuthenticated

# ==============================================================================
#                      1. CORE MODULAR PRODUCT VIEWSET (HYBRID/NESTED)
# ==============================================================================
class ModularProductCategoryViewSet(TenantSafeViewSetMixin,viewsets.ModelViewSet):
    """
    Provides full CRUD for Categories.
    The nested 'types' field is read-only, ensuring only Category data is written here.
    """
    queryset = ModularProductCategory.objects.all().prefetch_related(
        'modularproducttype_set',
        'modularproducttype_set__modularproductmodel_set'
    )
    serializer_class = ModularProductCategorySerializer
    permission_classes = [IsAuthenticated] 

class ModularProductTypeViewSet(TenantSafeViewSetMixin,viewsets.ModelViewSet):
    """
    Provides full CRUD for Product Types.
    Requires 'category' FK ID on creation/update.
    Filters product types based on the 'category' query parameter.
    """
    queryset = ModularProductType.objects.all().prefetch_related('modularproductmodel_set')
    serializer_class = ModularProductTypeSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        """
        Optionally filters the queryset by category if the 'category' query parameter is provided.
        """
        queryset = ModularProductType.objects.all().prefetch_related('modularproductmodel_set')
        
        # Get the 'category' query parameter from the request
        category_id = self.request.query_params.get('category', None)
        
        if category_id is not None:
            # Filter the queryset by the category_id if it's provided
            queryset = queryset.filter(category_id=category_id)
        
        return queryset

class ModularProductModelViewSet(TenantSafeViewSetMixin,viewsets.ModelViewSet):
    """
    Provides full CRUD for Product Models.
    Requires 'type' FK ID on creation/update.
    Filters product models based on the 'type' query parameter.
    """
    queryset = ModularProductModel.objects.all()
    serializer_class = ModularProductModelSerializer
    permission_classes = [IsAuthenticated]  

    def get_queryset(self):
        """
        Optionally filters the queryset by type if the 'type' query parameter is provided.
        """
        queryset = ModularProductModel.objects.all()

        # Get the 'type' query parameter from the request
        type_id = self.request.query_params.get('type', None)

        if type_id is not None:
            # Filter the queryset by the type_id if it's provided
            queryset = queryset.filter(type_id=type_id)

        return queryset

class ModularProductViewSet(TenantSafeViewSetMixin,viewsets.ModelViewSet):
    serializer_class = ModularProductSerializer

    queryset = ModularProduct.objects.all().prefetch_related(
        "parameters",
        "hardware_rules",
        "part_templates",
        "part_templates__material_whitelist",
        "part_templates__edgeband_whitelist",
        "part_templates__hardware_rules",
    ).select_related(
        "category",
        "type",
        "productmodel"
    )

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            "category",
            "type",
            "productmodel"
        ).prefetch_related(
            "parameters",
            "hardware_rules",
            "part_templates",
            "part_templates__material_whitelist",
            "part_templates__edgeband_whitelist",
            "part_templates__hardware_rules",
        )

        # ---------- FILTERS ----------
        category = self.request.query_params.get("category")
        type_ = self.request.query_params.get("type")
        model = self.request.query_params.get("model")
        search = self.request.query_params.get("search")

        if category:
            qs = qs.filter(category_id=category)

        if type_:
            qs = qs.filter(type_id=type_)

        if model:
            qs = qs.filter(productmodel_id=model)

        # ---------- ADVANCED SEARCH ----------
        if search:
            qs = qs.filter(
                Q(name__istartswith=search) |
                Q(name__icontains=search) |
                Q(productmodel__name__istartswith=search) |
                Q(category__name__istartswith=search) |
                Q(type__name__istartswith=search)
            ).distinct()

        return qs.order_by("name")

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        original = self.get_object()
        tenant = request.user.tenant

        with transaction.atomic():
            # 1. CLONE PARENT (Product)
            # We use a suffix and timestamp for enterprise audit tracking
            new_product = original
            new_product.pk = None
            new_product.id = None 
            new_product.name = f"{original.name} (Copy - {timezone.now().strftime('%Y-%m-%d')})"
            part.tenant = tenant
            new_product.save()

            # 2. BULK CLONE PARAMETERS
            params = []
            for p in original.parameters.all():
                p.pk = None
                p.product = new_product
                params.append(p)
            original.parameters.model.objects.bulk_create(params)

            # 3. BULK CLONE HARDWARE (Product Level)
            hw_rules = []
            for hr in original.hardware_rules.all():
                hr.pk = None
                hr.product = new_product
                hw_rules.append(hr)
            original.hardware_rules.model.objects.bulk_create(hw_rules)

            # 4. DEEP CLONE PART TEMPLATES (Nested relationships)
            for part in original.part_templates.all():
                old_part_pk = part.pk
                
                # Clone Part Template
                part.pk = None
                part.product = new_product
                part.save() # Save here to get a PK for the nested children
                
                # Clone Material Whitelists for this part
                mats = []
                for m in PartMaterialWhitelist.objects.filter(part_template_id=old_part_pk):
                    m.pk = None
                    m.part_template = part
                    mats.append(m)
                PartMaterialWhitelist.objects.bulk_create(mats)

                # Clone Hardware Rules for this part
                part_hws = []
                for phw in PartHardwareRule.objects.filter(part_template_id=old_part_pk):
                    phw.pk = None
                    phw.part_template = part
                    part_hws.append(phw)
                PartHardwareRule.objects.bulk_create(part_hws)
                
                # Clone Edgeband Whitelist (The enterprise piece we added)
                eb_white = []
                for eb in PartEdgeBandWhitelist.objects.filter(part_template_id=old_part_pk):
                    eb.pk = None
                    eb.part_template = part
                    eb_white.append(eb)
                PartEdgeBandWhitelist.objects.bulk_create(eb_white)

            return Response({"status": "Success", "new_id": new_product.id, "name": new_product.name})


# ==============================================================================
#                      2. MATERIAL VIEWSETS FOR FRONTEND DROPDOWNS
# ==============================================================================
# modular_calc/views.py

class WoodEnFilterViewSet(TenantSafeViewSetMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Provides all WoodEn materials, filtered by thickness, and unique thicknesses."""
    
    # 🎯 1. Set the final, ordered queryset as a class attribute
    # This ordering handles the hierarchy: material_grp (Category) -> material_type (Type) -> material_model (Model)
    queryset = WoodMaterial.objects.all().order_by(
        'material_grp__name', 
        'material_type__name', 
        'material_model__name'
    )
    
    serializer_class = WoodEnMiniSerializer 
    permission_classes = [IsAuthenticated]
    # 🎯 2. Define filter backends
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    
    # 🎯 3. Define fields available for filtering via query parameters
    filterset_fields = [
        'thickness_value', 
        'material_grp__name',
        'material_type__name',
        'material_model__name',
    ]

    # Optional: If you want to allow dynamic ordering via 'ordering' query param:
    ordering_fields = ['thickness_value', 'material_grp__name', 'material_type__name', 'material_model__name']
    
    @action(detail=False, methods=['get'], url_path='unique_thicknesses')
    def unique_thicknesses(self, request):
        """Returns a list of all unique thicknesses (Decimals) from WoodEn model."""
        # This method is correct and relies only on WoodEn model fields, not filters
        thicknesses = WoodMaterial.objects.values_list('thickness_value', flat=True).annotate(
            thickness_decimal=Cast('thickness_value', output_field=DecimalField())
        ).order_by('thickness_decimal').distinct()
        
        return Response([str(t) for t in thicknesses if t is not None])


class EdgeBandFilterViewSet(TenantSafeViewSetMixin, mixins.ListModelMixin, viewsets.GenericViewSet):

    # Set the default hierarchical ordering
    # We order by brand name and then the nested edgeband name
    queryset = EdgeBand.objects.all().order_by('edgeband_name__name')
    serializer_class = EdgeBandMiniSerializer
    permission_classes = [IsAuthenticated]
    # Enable explicit ordering via query parameters
    filter_backends = [OrderingFilter]
    ordering_fields = ['e_thickness', 'edgeband_name__name']
    ordering = [ 'edgeband_name__name'] # Default ordering

    def get_queryset(self):
        """
        Filters edgebands based on max_thickness_mm query parameter (derived from material thickness).
        The range is: e_thickness must be between [material_thickness + 0] and [material_thickness + 5].
        """
        queryset = self.queryset
        
        # max_thickness is the thickness of the material part (e.g., 18mm)
        material_thickness_str = self.request.query_params.get('material_thickness_mm') 

        if material_thickness_str:
            try:
                material_thickness = Decimal(material_thickness_str)
                
                min_t = material_thickness + 0  
                max_t = material_thickness + 5  
                
                # Filter for edgebands where e_thickness is within the calculated range
                queryset = queryset.filter(e_thickness__gte=min_t, e_thickness__lte=max_t) 
                
            except ValueError:
                # If material_thickness_str is not a valid number, ignore the filter
                pass
        
        return queryset

class HardwareFilterViewSet(TenantSafeViewSetMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    
    # 🎯 1. Optimized Queryset
    # Added select_related to prevent N+1 queries when fetching group and brand names
    queryset = Hardware.objects.select_related('h_group', 'brand', 'billing_unit').all().order_by(
        'h_group__name',      # Category
        'brand__name',        # Brand
        'h_name'              # Item Name
    )
    
    serializer_class = HardwareMiniSerializer 
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    
    # 🎯 2. Define fields available for filtering
    filterset_fields = [
        'h_group__name',     
        'brand__name',        
        'billing_unit__name', # FIXED: Changed 'unit' to 'billing_unit__name'
        'is_active',          # Optional: added this from your shell list
    ]
    
    # 🎯 3. Explicit fields for ordering
    # FIXED: Removed p_price, s_price, sl_price. Used cost_price and sell_price.
    ordering_fields = [
        'h_group__name', 
        'brand__name', 
        'h_name', 
        'cost_price', 
        'sell_price'
    ]# ==============================================================================
#                      3. UI UTILITY VIEWS
# ==============================================================================
    

def modular_config_ui(request):
    """View for serving the main UI template that uses the nested API."""
    # Assuming you have a template named 'modular_config_ui.html' for your single architecture
    return render(request, 'add_productjsthtml.html')

def modular_config_ui_copy(request):
    """View for serving the main UI template that uses the nested API."""
    # Assuming you have a template named 'modular_config_ui.html' for your single architecture
    return render(request, 'modular_config_ui_copy.html')
@login_required(login_url="/accounts/login/")
def layout_design(request):
    return render(request,'rebuiltmodular.html')
@login_required(login_url="/accounts/login/")
def add_product(request):
    return render(request,"modular_ui_a.html")

from django.shortcuts import render, get_object_or_404
from modular_calc.models import PartTemplate, ModularProduct
from modular_calc.evaluation.part_evaluator import PartEvaluator
from decimal import Decimal

def part_evaluation_test(request, product_id):
    product = get_object_or_404(ModularProduct, pk=product_id)
    parts_templates = product.part_templates.all()

    product_dims = {
        "product_length": Decimal(request.GET.get("product_length", 1000)),
        "product_width": Decimal(request.GET.get("product_width", 500)),
        "product_height": Decimal(request.GET.get("product_height", 800)),
    }

    evaluated_parts = []
    for pt in parts_templates:
        evaluator = PartEvaluator(pt, product_dims, parameters={})
        evaluated_parts.append(evaluator.evaluate())

    return render(request, "modular_calc/part_evaluation_test.html", {
        "parts": evaluated_parts,
        **product_dims
    })

