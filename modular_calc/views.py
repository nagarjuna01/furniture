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
from django.shortcuts import render
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
class ModularProductCategoryViewSet(viewsets.ModelViewSet):
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

class ModularProductTypeViewSet(viewsets.ModelViewSet):
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
    



class ModularProductModelViewSet(viewsets.ModelViewSet):
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

class ModularProductViewSet(viewsets.ModelViewSet):
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
        qs = ModularProduct.objects.all().select_related(
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





# ==============================================================================
#                      2. MATERIAL VIEWSETS FOR FRONTEND DROPDOWNS
# ==============================================================================
# modular_calc/views.py

class WoodEnFilterViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Provides all WoodEn materials, filtered by thickness, and unique thicknesses."""
    
    # 🎯 1. Set the final, ordered queryset as a class attribute
    # This ordering handles the hierarchy: material_grp (Category) -> material_type (Type) -> material_model (Model)
    queryset = WoodMaterial.objects.all().order_by(
        'material_grp__name', 
        'material_type__name', 
        'material_model__name'
    )
    
    serializer_class = WoodEnMiniSerializer 
    
    # 🎯 2. Define filter backends
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    
    # 🎯 3. Define fields available for filtering via query parameters
    filterset_fields = [
        'thickness', 
        'material_grp__name',
        'material_type__name',
        'material_model__name',
    ]

    # Optional: If you want to allow dynamic ordering via 'ordering' query param:
    ordering_fields = ['thickness', 'material_grp__name', 'material_type__name', 'material_model__name']
    
    @action(detail=False, methods=['get'], url_path='unique_thicknesses')
    def unique_thicknesses(self, request):
        """Returns a list of all unique thicknesses (Decimals) from WoodEn model."""
        # This method is correct and relies only on WoodEn model fields, not filters
        thicknesses = WoodMaterial.objects.values_list('thickness', flat=True).annotate(
            thickness_decimal=Cast('thickness', output_field=DecimalField())
        ).order_by('thickness_decimal').distinct()
        
        return Response([float(t) for t in thicknesses])


class EdgeBandFilterViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    # Set the default hierarchical ordering
    # We order by brand name and then the nested edgeband name
    queryset = EdgeBand.objects.all().order_by('brand__name', 'edgeband_name__name')
    serializer_class = EdgeBandMiniSerializer
    
    # Enable explicit ordering via query parameters
    filter_backends = [OrderingFilter]
    ordering_fields = ['e_thickness', 'brand__name', 'edgeband_name__name']
    ordering = ['brand__name', 'edgeband_name__name'] # Default ordering

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
                material_thickness = float(material_thickness_str)
                
                min_t = material_thickness + 0  
                max_t = material_thickness + 5  
                
                # Filter for edgebands where e_thickness is within the calculated range
                queryset = queryset.filter(e_thickness__gte=min_t, e_thickness__lte=max_t) 
                
            except ValueError:
                # If material_thickness_str is not a valid number, ignore the filter
                pass
        
        return queryset

class HardwareFilterViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    
    # 🎯 1. Set the default hierarchical ordering 
    # Order: Hardware Group -> Brand -> Hardware Name
    queryset = Hardware.objects.all().order_by(
        'h_group__name',      # Category
        'brand__name',        # Brand
        'h_name'              # Item Name
    )
    serializer_class = HardwareMiniSerializer 
    
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    
    # 🎯 2. Define fields available for filtering
    filterset_fields = [
        # Allows filtering by the name of the related objects
        'h_group__name',     
        'brand__name',        
        'unit',
        # You could add filtering by price ranges here if needed
    ]
    
    # Optional: Set the explicit fields that can be ordered by query param
    ordering_fields = ['h_group__name', 'brand__name', 'h_name', 'p_price', 's_price', 'sl_price']
# ==============================================================================
#                      3. UI UTILITY VIEWS
# ==============================================================================
    


def modular_config_ui(request):
    """View for serving the main UI template that uses the nested API."""
    # Assuming you have a template named 'modular_config_ui.html' for your single architecture
    return render(request, 'modular_config_ui.html')

def modular_config_ui_copy(request):
    """View for serving the main UI template that uses the nested API."""
    # Assuming you have a template named 'modular_config_ui.html' for your single architecture
    return render(request, 'modular_config_ui_copy.html')

def layout_design(request):
    return render(request,'rebuiltmodular.html')
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
