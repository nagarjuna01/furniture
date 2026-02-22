from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import render
from rest_framework.filters import SearchFilter, OrderingFilter

from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from accounts.mixins import TenantSafeViewSetMixin
from django_filters.rest_framework import DjangoFilterBackend

from .filters import ProductFilter,ProductVariantFilter

from .models import (
    Product,
    ProductType,
    ProductSeries,
    ProductVariant,
    ProductImage,
    VariantImage,
    AttributeDefinition,
    VariantAttributeValue,
    ProductBundle,
    ProductTemplate,
)

from .serializers import (
    ProductTypeSerializer,
    ProductSeriesSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductVariantSerializer,
    ProductImageSerializer,
    VariantImageSerializer,
    AttributeDefinitionSerializer,
    VariantAttributeValueSerializer,
    ProductWriteSerializer,ProductTemplateSerializer
)

# -------------------------------------------------------------------
# MASTER / GLOBAL DATA (READ ONLY)
# -------------------------------------------------------------------

class ProductTypeViewSet(TenantSafeViewSetMixin, ModelViewSet):
    queryset = ProductType.objects.all()
    serializer_class = ProductTypeSerializer
    permission_classes = [IsAuthenticated]


class ProductSeriesViewSet(TenantSafeViewSetMixin, ModelViewSet):
    queryset = ProductSeries.objects.select_related("product_type")
    serializer_class = ProductSeriesSerializer
    permission_classes = [IsAuthenticated]


class ProductViewSet(TenantSafeViewSetMixin, ModelViewSet):
    queryset = Product.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name", "sku"]
    ordering_fields = ["created_at", "name"]
    def get_queryset(self):
        qs = Product.objects.select_related(
            "product_type",
            "product_series"
        ).prefetch_related(
            "variants"
        )

        print("DEBUG Products:", qs.count())
        return super().get_queryset().select_related(
            "product_type",
            "product_series"
        ).prefetch_related("variants")

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        elif self.action == "retrieve":
            return ProductDetailSerializer
        return ProductWriteSerializer

class ProductVariantViewSet(TenantSafeViewSetMixin, ModelViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductVariantFilter
    search_fields = ["sku"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        # Tenant filtering
        if hasattr(user, "tenant"):
            qs = qs.filter(tenant=user.tenant)

        # Filter by product_id if provided
        product_id = self.request.query_params.get("product_id")
        if product_id:
            qs = qs.filter(product_id=product_id)

        # Optimize
        return qs.select_related("product", "measurement_unit", "billing_unit").prefetch_related("images", "attributes__attribute")

class AttributeDefinitionViewSet(TenantSafeViewSetMixin, ModelViewSet):
    queryset = AttributeDefinition.objects.all()
    serializer_class = AttributeDefinitionSerializer
    permission_classes = [IsAuthenticated]

class VariantAttributeValueViewSet(TenantSafeViewSetMixin, ModelViewSet):
    queryset = VariantAttributeValue.objects.all()
    serializer_class = VariantAttributeValueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        variant_id = self.kwargs.get("variant_pk")
        qs = VariantAttributeValue.objects.select_related(
            "variant",
            "attribute"
        )

        if variant_id:
            qs = qs.filter(variant_id=variant_id)

        return super().get_queryset().select_related(
            "variant",
            "attribute"
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["variant"] = ProductVariant.objects.get(
            id=self.kwargs["variant_pk"]
        )
        return context

class ProductImageViewSet(TenantSafeViewSetMixin, ModelViewSet):
    serializer_class = ProductImageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = ProductImage.objects.select_related("product")
        return super().get_queryset().select_related("product")

class VariantImageViewSet(TenantSafeViewSetMixin, ModelViewSet):
    serializer_class = VariantImageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = VariantImage.objects.select_related("variant")
        return super().get_queryset().select_related("variant")


# products1/views.py
from rest_framework import viewsets, filters
from products1.serializers import ProductBundleSerializer
 
class ProductBundleViewSet(viewsets.ModelViewSet):
    queryset = ProductBundle.objects.all()
    serializer_class = ProductBundleSerializer
    
    # ADD THESE TWO LINES:
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description'] # Fields you want to search

# catalog/views.py
from rest_framework import filters

class ProductTemplateViewSet(viewsets.ModelViewSet):
    queryset = ProductTemplate.objects.all()
    serializer_class = ProductTemplateSerializer
    
    # CRITICAL: Without these, ?search= won't work!
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'sku', 'description']
    def get_queryset(self):
    # Ensure templates are filtered by the active site/tenant
        return ProductTemplate.objects.filter(tenant=self.request.user.tenant)

# -------------------------------------------------------------------
# FRONTEND VIEWS
# -------------------------------------------------------------------
from django.views.decorators.cache import never_cache
@login_required
@never_cache
def product_management_view(request):
    """
    Renders the complete product & variant management page.
    All CRUD actions are handled via AJAX calls to DRF endpoints.
    """
    return render(request, "products/product_list.html")

@login_required(login_url="/accounts/login/")
def master_admin_view(request):
    return render(request, "products/admin_master1.html")


def customer_product_list(request):
    return render(request, "customer_product_list.html")
