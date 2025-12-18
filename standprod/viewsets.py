from rest_framework import viewsets, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .models import *
from .serializers import *


# -------------------------------------------------
# GLOBAL PAGINATION (10 per page default)
# -------------------------------------------------
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


# -------------------------------------------------
# TENANT FILTER MIXIN
# -------------------------------------------------
class TenantFilterMixin:
    """
    Auto-apply tenant filter when model has tenant field.
    """

    def get_queryset(self):
        base_qs = super().get_queryset()
        tenant = getattr(self.request.user, "tenant", None)

        if tenant and hasattr(base_qs.model, "tenant"):
            return base_qs.filter(tenant=tenant)

        return base_qs

    # Ensures serializer sees tenant
    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["tenant"] = getattr(self.request.user, "tenant", None)
        return ctx

class MeasurementUnitViewSet(viewsets.ModelViewSet):
    serializer_class = MeasurementUnitSerializer

    def get_queryset(self):
        tenant = getattr(self.request.user, "tenant", None)

        return MeasurementUnit.objects.filter(
            models.Q(tenant__isnull=True) | models.Q(tenant=tenant)
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["tenant"] = getattr(self.request.user, "tenant", None)
        return ctx


class BillingUnitViewSet(viewsets.ModelViewSet):
    serializer_class = BillingUnitSerializer

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        return BillingUnit.objects.filter(tenant=tenant)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["tenant"] = getattr(self.request, "tenant", None)
        return ctx

# -------------------------------------------------
# PRODUCT CORE
# -------------------------------------------------
class ProductViewSet(TenantFilterMixin, viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


class ProductVariantViewSet(TenantFilterMixin, viewsets.ModelViewSet):
    serializer_class = ProductVariantSerializer
    queryset = ProductVariant.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    # ADD FILTER FOR ?product=<id>
    def get_queryset(self):
        qs = super().get_queryset()
        product_id = self.request.query_params.get("product")

        if product_id:
            qs = qs.filter(product_id=product_id)

        return qs


class ProductTypeViewSet(TenantFilterMixin, viewsets.ModelViewSet):
    serializer_class = ProductTypeSerializer
    queryset = ProductType.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


class ProductModelViewSet(TenantFilterMixin, viewsets.ModelViewSet):
    serializer_class = ProductModelSerializer
    queryset = ProductModel.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


class ProductImageViewSet(TenantFilterMixin, viewsets.ModelViewSet):
    serializer_class = ProductImageSerializer
    queryset = ProductImage.objects.all()
    permission_classes = [permissions.IsAuthenticated]


class VariantImageViewSet(TenantFilterMixin, viewsets.ModelViewSet):
    serializer_class = VariantImageSerializer
    queryset = VariantImage.objects.all()
    permission_classes = [permissions.IsAuthenticated]


# -------------------------------------------------
# ATTRIBUTE SYSTEM
# -------------------------------------------------
class AttributeDefinitionViewSet(TenantFilterMixin, viewsets.ModelViewSet):
    serializer_class = AttributeDefinitionSerializer
    queryset = AttributeDefinition.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


class VariantAttributeValueViewSet(TenantFilterMixin, viewsets.ModelViewSet):
    serializer_class = VariantAttributeValueSerializer
    queryset = VariantAttributeValue.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination


# -------------------------------------------------
# OPTIONAL MODULES (TENANT MODULE CONTROL)
# -------------------------------------------------
def check_module_enabled(request, module_name):
    tenant = getattr(request.user, "tenant", None)
    if not tenant:
        return False
    return tenant.modules.filter(module_name=module_name, is_enabled=True).exists()


class DiscountViewSet(TenantFilterMixin, viewsets.ModelViewSet):
    serializer_class = DiscountSerializer
    queryset = Discount.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if not check_module_enabled(self.request, "discount"):
            return Discount.objects.none()
        return super().get_queryset()


class SupplierViewSet(TenantFilterMixin, viewsets.ModelViewSet):
    serializer_class = SupplierSerializer
    queryset = Supplier.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if not check_module_enabled(self.request, "supplier"):
            return Supplier.objects.none()
        return super().get_queryset()


class WorkOrderViewSet(TenantFilterMixin, viewsets.ModelViewSet):
    serializer_class = WorkOrderSerializer
    queryset = WorkOrder.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if not check_module_enabled(self.request, "workorder"):
            return WorkOrder.objects.none()
        return super().get_queryset()


class ShippingMethodViewSet(TenantFilterMixin, viewsets.ModelViewSet):
    serializer_class = ShippingMethodSerializer
    queryset = ShippingMethod.objects.all()
    permission_classes = [permissions.IsAuthenticated]


class ShipmentViewSet(TenantFilterMixin, viewsets.ModelViewSet):
    serializer_class = ShipmentSerializer
    queryset = Shipment.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if not check_module_enabled(self.request, "shipping"):
            return Shipment.objects.none()
        return super().get_queryset()


class ProductReviewViewSet(TenantFilterMixin, viewsets.ModelViewSet):
    serializer_class = ProductReviewSerializer
    queryset = ProductReview.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if not check_module_enabled(self.request, "review"):
            return ProductReview.objects.none()
        return super().get_queryset()
