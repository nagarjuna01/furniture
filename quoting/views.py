from rest_framework import viewsets, status, decorators
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from accounts.mixins import TenantSafeViewSetMixin
from rest_framework.permissions import IsAuthenticated, AllowAny
from modular_calc.models import ModularProduct
from .models import QuoteRequest, QuoteProduct, QuotePart, OverrideLog
from .serializers import QuoteRequestSerializer, QuoteProductSerializer, QuotePartSerializer,MarketplaceQuoteSerializer,TenantQuoteSerializer
from modular_calc.evaluation.part_evaluator import PartEvaluator
from material.models.wood import WoodMaterial
from accounts.mixins import TenantSafeMixin
from .visuals.services import render_svg

# 1. MARKETPLACE CATALOG (Public Lead Generation)
# ---------------------------------------------------------
class MarketplaceCatalogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Used by public customers to browse all public products across ALL tenants.
    """
    permission_classes = [AllowAny]
    queryset = ModularProduct.objects.filter(is_public=True)
    # Use a basic serializer for the catalog list
    # serializer_class = ModularProductSerializer 


class QuoteRequestViewSet(TenantSafeMixin, viewsets.ModelViewSet):
    queryset = QuoteRequest.objects.all().prefetch_related("products")
    serializer_class = QuoteRequestSerializer

class QuoteProductViewSet(TenantSafeMixin, viewsets.ModelViewSet):
    queryset = QuoteProduct.objects.select_related("product_template", "quote")
    serializer_class = QuoteProductSerializer

    def get_serializer_class(self):
        # Switch serializer based on who is looking
        if self.request.query_params.get('portal') == 'marketplace':
            return MarketplaceQuoteSerializer
        
        if self.request.user.is_staff:
            return TenantQuoteSerializer
            
        return QuoteProductSerializer

    def perform_create(self, serializer):
        """
        Custom create to handle Lead Generation logic.
        """
        # 1. If Marketplace portal, we assign tenant from the PRODUCT template owner
        if self.request.query_params.get('portal') == 'marketplace':
            product_template = serializer.validated_data['product_template']
            instance = serializer.save(tenant=product_template.tenant)
            self.notify_factory_of_new_lead(instance)
        else:
            # 2. If internal, use the worker's tenant
            serializer.save(tenant=self.request.user.tenant)

    @decorators.action(detail=True, methods=['post'])
    def expand(self, request, pk=None):
        """
        FREEZE geometry and generate production parts (Staff Only).
        """
        product = self.get_object()
        
        if not request.user.is_staff:
            return Response({"error": "Manufacturing data is restricted"}, status=403)
            
        count = product.expand_to_parts()
        return Response({
            "status": "Success", 
            "parts_generated": count,
            "total_factory_cost": product.total_cp
        })

    def notify_factory_of_new_lead(self, instance):
        # Logic for Email/Dashboard Alert to the Tenant
        print(f"ALERT: Tenant {instance.tenant.id} has a new Marketplace Lead!")

class QuotePartViewSet(viewsets.ModelViewSet):
    queryset = QuotePart.objects.select_related("quote_product", "part_template", "material")
    serializer_class = QuotePartSerializer

    @action(detail=True, methods=["post"])
    def override_material(self, request, pk=None):
        qp = self.get_object()
        old = qp.material
        new_id = request.data.get("material")
        reason = request.data.get("reason", "")

        if not new_id:
            return Response({"detail": "material required"}, status=400)

        new = WoodEn.objects.get(pk=new_id)

        # Warn if thickness mismatch
        warn = None
        if str(new.thickness_mm) != str(qp.thickness_mm):
            warn = f"Material thickness {new.thickness_mm} != part thickness {qp.thickness_mm}"

        qp.material = new
        qp.override_by_employee = True
        qp.override_reason = reason
        qp.save()

        OverrideLog.objects.create(
            quote_part=qp,
            field="material",
            old_value=str(old) if old else "",
            new_value=str(new),
            reason=reason,
            changed_by=request.user if request.user.is_authenticated else None
        )
        return Response({"ok": True, "warning": warn})
