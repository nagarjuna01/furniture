from django.db import transaction
from django.shortcuts import render
from django.views.generic import TemplateView

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import (
    Product,
    ProductType,
    ProductSeries,
    BillingUnit,
    MeasurementUnit,
    AttributeDefinition,
    ProductVariant,
    ProductImage,
    VariantImage,
)

from .serializers import (
    ProductSerializer,
    ProductTypeSerializer,
    ProductSeriesSerializer,
    BillingUnitSerializer,
    MeasurementUnitSerializer,
    AttributeDefinitionSerializer,
    ProductVariantSerializer,
    ProductImageSerializer,
    VariantImageSerializer,
)

# -------------------------------------------------------------------
# MASTER DATA VIEWSETS
# -------------------------------------------------------------------

class ProductTypeViewSet(viewsets.ModelViewSet):
    queryset = ProductType.objects.all()
    serializer_class = ProductTypeSerializer


class ProductSeriesViewSet(viewsets.ModelViewSet):
    queryset = ProductSeries.objects.select_related("product_type")
    serializer_class = ProductSeriesSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["product_type"]


class BillingUnitViewSet(viewsets.ModelViewSet):
    queryset = BillingUnit.objects.all()
    serializer_class = BillingUnitSerializer


class MeasurementUnitViewSet(viewsets.ModelViewSet):
    queryset = MeasurementUnit.objects.all()
    serializer_class = MeasurementUnitSerializer


class AttributeDefinitionViewSet(viewsets.ModelViewSet):
    queryset = AttributeDefinition.objects.all()
    serializer_class = AttributeDefinitionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["field_type"]
    search_fields = ["name"]

# -------------------------------------------------------------------
# PRODUCT VIEWSET
# -------------------------------------------------------------------

class ProductViewSet(viewsets.ModelViewSet):
    queryset = (
        Product.objects
        .select_related("product_type", "product_series")
        .prefetch_related("variants__images", "images")
    )
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["product_type", "is_active"]
    search_fields = ["name", "sku"]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @swagger_auto_schema(
        request_body=ProductSerializer,
        consumes=["application/json", "multipart/form-data"],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=ProductSerializer,
        consumes=["application/json", "multipart/form-data"],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    # ------------------ PRODUCT IMAGE UPLOAD ------------------

    @action(
        detail=True,
        methods=["post"],
        parser_classes=[MultiPartParser],
        url_path="upload-images",
    )
    def upload_images(self, request, pk=None):
        product = self.get_object()
        files = request.FILES.getlist("images")

        if not files:
            return Response(
                {"detail": "No images provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        created = []
        for file in files:
            img = ProductImage.objects.create(
                product=product,
                image=file
            )
            created.append(img)

        return Response(
            ProductImageSerializer(
                created, many=True, context={"request": request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    # ------------------ SET PRIMARY IMAGE ------------------

    @action(detail=True, methods=["post"])
    def set_primary_image(self, request, pk=None):
        product = self.get_object()
        image_id = request.data.get("image_id")

        if not image_id:
            return Response(
                {"detail": "image_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                ProductImage.objects.filter(
                    product=product
                ).update(is_primary=False)

                image = ProductImage.objects.get(
                    id=image_id, product=product
                )
                image.is_primary = True
                image.save()

        except ProductImage.DoesNotExist:
            return Response(
                {"detail": "Invalid image_id"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({"status": "primary image set"})

    # ------------------ DELETE IMAGE ------------------

    @action(
        detail=True,
        methods=["delete"],
        url_path="delete-image/(?P<image_id>[^/.]+)",
    )
    def delete_image(self, request, pk=None, image_id=None):
        product = self.get_object()

        try:
            image = ProductImage.objects.get(
                id=image_id, product=product
            )
            image.delete()
        except ProductImage.DoesNotExist:
            return Response(
                {"detail": "Image not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({"status": "image deleted"})

# -------------------------------------------------------------------
# PRODUCT VARIANT VIEWSET
# -------------------------------------------------------------------

class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = (
        ProductVariant.objects
        .select_related("product", "measurement_unit", "billing_unit")
        .prefetch_related("attributes__attribute", "images")
    )
    serializer_class = ProductVariantSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @swagger_auto_schema(
        request_body=ProductVariantSerializer,
        consumes=["application/json", "multipart/form-data"],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=ProductVariantSerializer,
        consumes=["application/json", "multipart/form-data"],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    # ------------------ VARIANT IMAGE UPLOAD ------------------

    @action(
        detail=True,
        methods=["post"],
        parser_classes=[MultiPartParser],
        url_path="upload-images",
    )
    def upload_images(self, request, pk=None):
        variant = self.get_object()
        files = request.FILES.getlist("images")

        if not files:
            return Response(
                {"detail": "No images provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        created = []
        for file in files:
            img = VariantImage.objects.create(
                variant=variant,
                image=file
            )
            created.append(img)

        return Response(
            VariantImageSerializer(
                created, many=True, context={"request": request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    # ------------------ SET PRIMARY IMAGE ------------------

    @action(detail=True, methods=["post"])
    def set_primary_image(self, request, pk=None):
        variant = self.get_object()
        image_id = request.data.get("image_id")

        if not image_id:
            return Response(
                {"detail": "image_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                VariantImage.objects.filter(
                    variant=variant
                ).update(is_primary=False)

                image = VariantImage.objects.get(
                    id=image_id, variant=variant
                )
                image.is_primary = True
                image.save()

        except VariantImage.DoesNotExist:
            return Response(
                {"detail": "Invalid image_id"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({"status": "primary variant image set"})

    # ------------------ DELETE IMAGE ------------------

    @action(
        detail=True,
        methods=["delete"],
        url_path="delete-image/(?P<image_id>[^/.]+)",
    )
    def delete_image(self, request, pk=None, image_id=None):
        variant = self.get_object()

        try:
            image = VariantImage.objects.get(
                id=image_id, variant=variant
            )
            image.delete()
        except VariantImage.DoesNotExist:
            return Response(
                {"detail": "Image not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({"status": "variant image deleted"})

# -------------------------------------------------------------------
# FRONTEND VIEWS
# -------------------------------------------------------------------

class ProductSPAView(TemplateView):
    template_name = "products/index.html"


def master_admin_view(request):
    return render(request, "products/admin_master1.html")


def customer_product_list(request):
    return render(request, "customer_product_list.html")
