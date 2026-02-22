from decimal import Decimal,InvalidOperation
import traceback

from django.db import transaction
from django.db.models import Q, DecimalField
from django.db.models.functions import Cast
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from modular_calc.evaluation.product_engine import ProductEngine

from accounts.mixins import TenantSafeViewSetMixin

from .models import (
    ModularProduct, ModularProductCategory, ModularProductModel, ModularProductType,
    PartTemplate, PartMaterialWhitelist, PartEdgeBandWhitelist, ProductHardwareRule,
    PartHardwareRule, ProductParameter
)
from .serializers import (
    ModularProductSerializer, DryRunSerializer,
    WoodEnMiniSerializer, HardwareMiniSerializer,
    EdgeBandMiniSerializer, ModularProductCategorySerializer,
    ModularProductModelSerializer, ModularProductTypeSerializer
)
from material.models.wood import WoodMaterial
from material.models.edgeband import EdgeBand
from material.models.hardware import Hardware

from .evaluation.bom_builder import BOMBuilder
from .evaluation.cutlist_optimizer import CutlistOptimizer
from .evaluation.validators import validate_boolean_expression
from .evaluation.context import ProductContext
from .evaluation.part_evaluator import PartEvaluator
from .utils.expression_templates import EXPRESSION_TEMPLATES
from .services.ai.expression_sugesstion import suggest_expression
from modular_calc.evaluation.product_engine import ProductEngine
from modular_calc.services.constraints.suggestion_engine import solve_constraints


class ModularProductCategoryViewSet(TenantSafeViewSetMixin, viewsets.ModelViewSet):
    queryset = ModularProductCategory.objects.all().prefetch_related(
        'modularproducttype_set', 'modularproducttype_set__modularproductmodel_set'
    )
    serializer_class = ModularProductCategorySerializer
    permission_classes = [IsAuthenticated]

class ModularProductTypeViewSet(TenantSafeViewSetMixin, viewsets.ModelViewSet):
    serializer_class = ModularProductTypeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = ModularProductType.objects.all().prefetch_related('modularproductmodel_set')
        category_id = self.request.query_params.get('category', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset
import inspect
class ModularProductModelViewSet(TenantSafeViewSetMixin, viewsets.ModelViewSet):
    serializer_class = ModularProductModelSerializer
    permission_classes = [IsAuthenticated]
    queryset = ModularProductModel.objects.all()
    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get("category")
        type_ = self.request.query_params.get("type")
        model = self.request.query_params.get("model")

        if category and category.isdigit(): qs = qs.filter(category_id=category)
        if type_ and type_.isdigit(): qs = qs.filter(type_id=type_)
        if model and model.isdigit(): qs = qs.filter(productmodel_id=model)

        return qs.order_by("name")

class ModularProductViewSet(TenantSafeViewSetMixin, viewsets.ModelViewSet):
    serializer_class = ModularProductSerializer
    permission_classes = [IsAuthenticated]
    queryset = ModularProduct.objects.all().select_related(
        "category", "type", "productmodel"
    ).prefetch_related(
        "parameters",
        "hardware_rules__hardware",
        "part_templates__hardware_rules__hardware",
        "part_templates__material_whitelist__material",
        "part_templates__material_whitelist__edgeband_options__edgeband", 
    )
    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get("category")
        type_ = self.request.query_params.get("type")
        model = self.request.query_params.get("model")
        search = self.request.query_params.get("search")

        if category: qs = qs.filter(category_id=category)
        if type_: qs = qs.filter(type_id=type_)
        if model: qs = qs.filter(productmodel_id=model)
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(productmodel__name__icontains=search) |
                Q(category__name__icontains=search) |
                Q(type__name__icontains=search)
            ).distinct()
        return qs.order_by("name")

    def _safe_float(self, val, default=0.0):
        """
        Force-convert any input to a standard Python float.
        This prevents the Decimal vs Float 'unsupported operand' crash.
        """
        try:
            if val is None: return float(default)
            if isinstance(val, Decimal): return float(val)
            # Remove units like 'mm' and cast to float
            clean_str = str(val).lower().replace('mm', '').strip()
            return float(clean_str)
        except (ValueError, TypeError):
            return float(default)

    def _deep_float_convert(self, obj):
        """
        Recursively converts all Decimals in a dictionary or list to floats.
        This is the final guardrail against 'unsupported operand' errors.
        """
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, dict):
            return {k: self._deep_float_convert(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._deep_float_convert(i) for i in obj]
        return obj

    @action(detail=True, methods=['post'])
    def evaluate(self, request, pk=None):
        product = self.get_object()
        data = request.data
        
        # 1. Material & Setup
        material_id = data.get("material_id")
        if not material_id:
            return Response({"error": "material_id is required"}, status=400) 
        
        selected_material = get_object_or_404(
            WoodMaterial, id=material_id, tenant=request.user.tenant
        )

        def safe_float(value, default=0.0):
            try:
                return float(value) if value is not None else float(default)
            except (ValueError, TypeError):
                return float(default)

        # 2. Dimensions
        L = safe_float(data.get("product_length") or data.get("L"), 1000)
        W = safe_float(data.get("product_width") or data.get("W"), 600)
        H = safe_float(data.get("product_height") or data.get("H"), 720)
        qty = int(safe_float(data.get("quantity") or 1))

        product_dims = {
            "L": L, "W": W, "H": H,
            "length": L, "width": W, "height": H,
            "product_length": L, "product_width": W, "product_height": H,
            "quantity": qty,
        }

        # 3. Parameters (Merge System Truth + User Overrides)
        # We fetch the clean abbreviations (D1FH, etc.) directly from the DB
        system_defaults = {
            p.abbreviation: safe_float(p.default_value) 
            for p in product.parameters.all()
        }

        raw_params = data.get("parameters") or data.get("custom_parameters") or {}
        user_overrides = {
            str(k): safe_float(v) for k, v in raw_params.items() 
            if isinstance(raw_params, dict)
        }

        # Final context for the engine
        cleaned_params = {**system_defaults, **user_overrides}
        
        quantities = [qty]
        if isinstance(data.get("quantities"), list):
            quantities = [int(safe_float(q)) for q in data.get("quantities")]

        # -------------------
        # 2️⃣ Run Engine
        # -------------------
        try:
            engine_payload = {
                "product": product,
                "product_dims": product_dims,
                "parameters": cleaned_params, # Contains D1FH from DB
                "quantities": quantities,
                "selected_material": selected_material,   
            }

            engine = ProductEngine(engine_payload)
            raw_output = engine.run()
            engine_output = self._deep_float_convert(raw_output)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": f"Engine calculation failed: {str(e)}"
            }, status=400)
        
        # -------------------
        # 3️⃣ AI & Constraints
        # -------------------
        ai_suggestions = []
        if "constraints" in data:
            for constraint_text in data["constraints"]:
                try:
                    ai_suggestions += suggest_expression(constraint_text, cleaned_params)
                except Exception: continue

        constraint_analysis = []
        target_var = data.get("target_variable")
        if target_var and "constraints" in data:
            for expr in data["constraints"]:
                try:
                    constraint_analysis.append(solve_constraints(expr, cleaned_params, target_var))
                except Exception: continue

        return Response({
            "engine_output": engine_output,
            "ai_suggestions": ai_suggestions,
            "constraint_analysis": constraint_analysis,
        }, status=200)
    @action(detail=True, methods=['post'], url_path='set-part-default-material')
    def set_part_default_material(self, request, pk=None):
        """
        Logic: Toggles the default material for a specific part template.
        Payload: {"part_template_id": 123, "material_whitelist_id": 456}
        """
        part_id = request.data.get("part_template_id")
        whitelist_id = request.data.get("material_whitelist_id")
        
        with transaction.atomic():
            # Reset all for this part
            PartMaterialWhitelist.objects.filter(
                part_template_id=part_id, 
                tenant=request.user.tenant
            ).update(is_default=False)
            
            # Set new default
            target = get_object_or_404(PartMaterialWhitelist, id=whitelist_id)
            target.is_default = True
            target.save()
            
        return Response({"status": "Default material updated"})

    @action(detail=False, methods=['post'], url_path='create_full')
    def create_full(self, request):
        """
        Refactored: Uses Serializer for nested creation of Product, Parts, 
        Material Whitelists, and Hardware Rules.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    # Pass tenant directly to the save method if your serializer handles it
                    product = serializer.save(tenant=request.user.tenant)
                    return Response({
                        "status": "Success",
                        "product_id": product.id,
                        "message": f"Global Engine: {product.name} created successfully."
                    }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": f"Creation failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        original = self.get_object()
        tenant = request.user.tenant
        try:
            with transaction.atomic():
                original_id = original.pk
                
                # 1. Clone Product
                # Use a fresh fetch to avoid session state issues
                new_product = ModularProduct.objects.get(pk=original_id)
                new_product.pk = None
                new_product.id = None 
                new_product.name = f"{original.name} (Copy - {timezone.now().strftime('%Y-%m-%d %H:%M')})"
                
                # Handle unique slug if it exists
                if hasattr(new_product, 'slug'):
                    new_product.slug = f"{getattr(original, 'slug', 'prod')}-{uuid.uuid4().hex[:6]}"
                
                new_product.tenant = tenant
                new_product.save()

                # 2. Clone Parameters Safely
                # Instead of mapping fields manually, we clone the object
                for p in ProductParameter.objects.filter(product_id=original_id):
                    p.pk = None
                    p.id = None
                    p.product = new_product
                    p.tenant = tenant
                    # Remove the 'datatype' assignment since it doesn't exist in your model
                    p.save()

                # 3. Clone Parts & Children
                for old_part in PartTemplate.objects.filter(product_id=original_id):
                    old_part_pk = old_part.pk
                    
                    # Clone PartTemplate
                    old_part.pk = None
                    old_part.id = None
                    old_part.product = new_product
                    old_part.tenant = tenant
                    old_part.save() 
                    new_part = old_part

                    # Clone Material Whitelists
                    for old_mat in PartMaterialWhitelist.objects.filter(part_template_id=old_part_pk):
                        old_mat_pk = old_mat.pk
                        new_mat = PartMaterialWhitelist.objects.create(
                            part_template=new_part, 
                            material=old_mat.material,
                            is_default=old_mat.is_default, 
                            tenant=tenant
                        )
                        
                        # Clone Edgeband options
                        eb_objs = []
                        for eb in PartEdgeBandWhitelist.objects.filter(material_selection_id=old_mat_pk):
                            eb_objs.append(PartEdgeBandWhitelist(
                                material_selection=new_mat, 
                                edgeband=eb.edgeband, 
                                side=eb.side, 
                                is_default=eb.is_default, 
                                tenant=tenant
                            ))
                        PartEdgeBandWhitelist.objects.bulk_create(eb_objs)

                return Response({"status": "Success", "new_id": new_product.id}, status=201)
        except Exception as e:
            # This will now catch the exact field name causing the issue
            return Response({"error": f"Duplication failed: {str(e)}"}, status=400)

class WoodEnFilterViewSet(TenantSafeViewSetMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = WoodMaterial.objects.all().order_by('material_grp__name', 'material_type__name', 'material_model__name')
    serializer_class = WoodEnMiniSerializer 
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['thickness_value', 'material_grp__name','material_type__name','material_model__name']

    @action(detail=False, methods=['get'], url_path='unique_thicknesses')
    def unique_thicknesses(self, request):
        thicknesses = WoodMaterial.objects.values_list('thickness_value', flat=True).annotate(
            thickness_decimal=Cast('thickness_value', output_field=DecimalField())
        ).order_by('thickness_decimal').distinct()
        return Response([str(t) for t in thicknesses if t is not None])

class EdgeBandFilterViewSet(TenantSafeViewSetMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = EdgeBand.objects.all().order_by('edgeband_name__name')
    serializer_class = EdgeBandMiniSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        material_id = self.request.query_params.get("material")
        if not material_id: return EdgeBand.objects.none()
        material = get_object_or_404(WoodMaterial, id=material_id, tenant=self.request.user.tenant)
        return EdgeBand.objects.filter(
            tenant=self.request.user.tenant, is_active=True,
            e_thickness__gt=material.thickness_value,
            e_thickness__lte=material.thickness_value + Decimal("5.0")
        ).select_related('edgeband_name')

class HardwareFilterViewSet(TenantSafeViewSetMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Hardware.objects.select_related('h_group', 'brand', 'billing_unit').all().order_by('h_group__name', 'brand__name', 'h_name')
    serializer_class = HardwareMiniSerializer 
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['h_group__name','brand__name','billing_unit__name', 'is_active']

class ExpressionValidateAPIView(APIView):
    permission_classes =[IsAuthenticated]
    def post(self, request):
        expr = request.data.get("expression")
        ctx = ProductContext(
            product_dims=request.data.get("product_dims", {}),
            parameters=request.data.get("parameters", {}),
            parts=request.data.get("parts", {})
        ).get_context()
        try:
            validate_boolean_expression(expr, ctx)
            return Response({"valid": True})
        except Exception as e:
            return Response({"valid": False, "error": str(e)}, status=400)

class ModularProductDryRunView(APIView):
    def post(self, request):
        serializer = DryRunSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            ctx = ProductContext(product_dims=data["product_dims"], parameters=data.get("parameters", []), parts=data["part_templates"])
            evaluator = PartEvaluator(parts=data["part_templates"], context=ctx.get_context())
            result = evaluator.evaluate_all()
            return Response({"preview": result}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=400)
class ExpressionTemplateListView(APIView):
    permission_classes= [IsAuthenticated]
    def get(self, request):
        return Response(EXPRESSION_TEMPLATES, status=status.HTTP_200_OK)

class ExpressionContextView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request, product_id):
        ctx = ProductContext.from_product(product_id)
        return Response(ctx.describe(), status=status.HTTP_200_OK)

class ExpressionSuggestionView(APIView):

    def post(self, request):
        intent = request.data.get("intent")
        context = ProductContext.from_product(request.data["product_id"])
        suggestion = suggest_expression(intent, context)
        return Response({"suggestion": suggestion}, status=status.HTTP_200_OK)

@login_required(login_url="/accounts/login/")
def modular_config_ui(request):
    return render(request, 'add_productjsthtml.html')

@login_required(login_url="/accounts/login/")
def modular_config_ui_copy(request):
    return render(request, 'modular_config_ui_copy.html')

@login_required(login_url="/accounts/login/")
def layout_design(request):
    return render(request,'rebuiltmodular.html')

@login_required(login_url="/accounts/login/")
def add_product(request):
    return render(request,"add_productjsthtml.html")

def add_part(request):
    edit_id = request.GET.get('edit_id')
    return render(request, "add_parts.html", {"edit_id": edit_id})

def product_output(request):
    product_id = request.GET.get('product_id')
    return render(request, "newio.html", {'product_id': product_id})
def new_output(request):
    return render(request, "newio.html")

@login_required(login_url="/accounts/login/")
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
