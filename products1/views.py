# from rest_framework import viewsets, filters, status,permissions
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework.parsers import MultiPartParser
# from django_filters.rest_framework import DjangoFilterBackend
# from django.views.generic import TemplateView
# from django.shortcuts import render
# from django.contrib.admin.views.decorators import staff_member_required
# from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
# from drf_yasg.utils import swagger_auto_schema # <-- Import this
# from drf_yasg import openapi # <-- Import this

# from .models import (
#     Product, ProductType, ProductModel, BillingUnit, MeasurementUnit,
#     AttributeDefinition, ProductVariant, ProductImage, VariantImage
# )
# from .serializers import (
#     ProductSerializer, ProductTypeSerializer, ProductModelSerializer,
#     BillingUnitSerializer, MeasurementUnitSerializer,
#     AttributeDefinitionSerializer, ProductVariantSerializer,
#     VariantImageSerializer
# )

# # --- Master Data ViewSets ---

# class ProductTypeViewSet(viewsets.ModelViewSet):
#     queryset = ProductType.objects.all()
#     serializer_class = ProductTypeSerializer


# class ProductModelViewSet(viewsets.ModelViewSet):
#     queryset = ProductModel.objects.select_related('type')
#     serializer_class = ProductModelSerializer
#     filter_backends = [DjangoFilterBackend]
#     filterset_fields = ['type']


# class BillingUnitViewSet(viewsets.ModelViewSet):
#     queryset = BillingUnit.objects.all()
#     serializer_class = BillingUnitSerializer


# class MeasurementUnitViewSet(viewsets.ModelViewSet):
#     queryset = MeasurementUnit.objects.all()
#     serializer_class = MeasurementUnitSerializer


# class AttributeDefinitionViewSet(viewsets.ModelViewSet):
#     queryset = AttributeDefinition.objects.all()
#     serializer_class = AttributeDefinitionSerializer
#     filter_backends = [DjangoFilterBackend, filters.SearchFilter]
#     filterset_fields = ['field_type', 'name']
#     search_fields = ['name']


# # --- Product ViewSet ---
# class ProductViewSet(viewsets.ModelViewSet):
#     queryset = Product.objects.prefetch_related('variants', 'images')
#     serializer_class = ProductSerializer
#     filter_backends = [DjangoFilterBackend, filters.SearchFilter]
#     filterset_fields = ['type', 'is_active']
#     search_fields = ['name', 'sku', 'type__name', 'model__name']
#     parser_classes = [MultiPartParser, FormParser, JSONParser] # <-- Add this to the main ViewSet

#     @swagger_auto_schema(
#         operation_description="Upload multiple images for a specific product.",
#         # --- CHANGE THIS PART ---
#         manual_parameters=[
#             # Define each expected form field as an openapi.Parameter
#             openapi.Parameter(
#                 name='images',
#                 in_=openapi.IN_FORM, # Indicates it's part of form data
#                 type=openapi.TYPE_ARRAY,
#                 items=openapi.Items(type=openapi.TYPE_FILE), # This describes a list of files
#                 required=True,
#                 description='List of image files to upload for the product'
#             ),
#             # If you were sending is_primary per image file like 'is_primary_0', 'is_primary_1' etc.
#             # you would list them individually here:
#             # openapi.Parameter(
#             #     name='is_primary_0', in_=openapi.IN_FORM, type=openapi.TYPE_BOOLEAN,
#             #     required=False, description='Is image 0 primary?'
#             # ),
#         ],
#         # --- END CHANGE ---
#         responses={
#             status.HTTP_201_CREATED: openapi.Response(
#                 description="Images uploaded successfully",
#                 schema=openapi.Schema(
#                     type=openapi.TYPE_OBJECT,
#                     properties={'status': openapi.Schema(type=openapi.TYPE_STRING)}
#                 )
#             ),
#             status.HTTP_400_BAD_REQUEST: "Bad Request"
#         }
#     )
#     @action(detail=True, methods=['post'], parser_classes=[MultiPartParser], url_path='upload-images')
#     def upload_images(self, request, pk=None):
#         product = self.get_object()
#         for file in request.FILES.getlist('images'):
#             ProductImage.objects.create(product=product, image=file)
#         return Response({'status': 'images uploaded'}, status=status.HTTP_201_CREATED)
# # class ProductViewSet(viewsets.ModelViewSet):
# #     queryset = Product.objects.prefetch_related('variants', 'images')
# #     serializer_class = ProductSerializer
# #     filter_backends = [DjangoFilterBackend, filters.SearchFilter]
# #     filterset_fields = ['type', 'is_active']
# #     search_fields = ['name', 'sku', 'type__name', 'model__name']

# #     @action(detail=True, methods=['post'], parser_classes=[MultiPartParser], url_path='upload-images')
# #     def upload_images(self, request, pk=None):
# #         product = self.get_object()
# #         for file in request.FILES.getlist('images'):
# #             ProductImage.objects.create(product=product, image=file)
# #         return Response({'status': 'images uploaded'}, status=status.HTTP_201_CREATED)

# class VariantImageViewSet(viewsets.ModelViewSet):
#     queryset = VariantImage.objects.all()
#     serializer_class = VariantImageSerializer
#     #permission_classes = [permissions.IsAuthenticated]  # or custom if needed
# # --- Product Variant ViewSet ---

# class ProductVariantViewSet(viewsets.ModelViewSet):
#     queryset = ProductVariant.objects.select_related(
#         'product', 'measurement_unit', 'billing_unit'
#     ).prefetch_related('attributes__attribute', 'images')
#     serializer_class = ProductVariantSerializer
#     parser_classes = [MultiPartParser, FormParser, JSONParser] # <-- Add this to the main ViewSet

#     @swagger_auto_schema(
#         operation_description="Upload multiple images for a specific product variant.",
#         # --- CHANGE THIS PART ---
#         manual_parameters=[
#             openapi.Parameter(
#                 name='images',
#                 in_=openapi.IN_FORM,
#                 type=openapi.TYPE_ARRAY,
#                 items=openapi.Items(type=openapi.TYPE_FILE),
#                 required=True,
#                 description='List of image files to upload for the variant'
#             ),
#         ],
#         # --- END CHANGE ---
#         responses={
#             status.HTTP_201_CREATED: openapi.Response(
#                 description="Variant images uploaded successfully",
#                 schema=openapi.Schema(
#                     type=openapi.TYPE_OBJECT,
#                     properties={'status': openapi.Schema(type=openapi.TYPE_STRING)}
#                 )
#             ),
#             status.HTTP_400_BAD_REQUEST: "Bad Request"
#         }
#     )
#     @action(detail=True, methods=['post'], parser_classes=[MultiPartParser], url_path='upload-images')
#     def upload_images(self, request, pk=None):
#         variant = self.get_object()
#         for file in request.FILES.getlist('images'):
#             VariantImage.objects.create(variant=variant, image=file)
#         return Response({'status': 'variant images uploaded'}, status=status.HTTP_201_CREATED)

# # class ProductVariantViewSet(viewsets.ModelViewSet):
# #     queryset = ProductVariant.objects.select_related(
# #         'product', 'measurement_unit', 'billing_unit'
# #     ).prefetch_related('attributes__attribute', 'images')
# #     serializer_class = ProductVariantSerializer

# #     @action(detail=True, methods=['post'], parser_classes=[MultiPartParser], url_path='upload-images')
# #     def upload_images(self, request, pk=None):
# #         variant = self.get_object()
# #         for file in request.FILES.getlist('images'):
# #             VariantImage.objects.create(variant=variant, image=file)
# #         return Response({'status': 'variant images uploaded'}, status=status.HTTP_201_CREATED)


# # --- Frontend SPA and Admin View ---

# class ProductSPAView(TemplateView):
#     template_name = "products/index.html"

# #@staff_member_required
# def master_admin_view(request):
#     return render(request, 'admin_master.html')

# def customer_product_list(request):
#     return render(request, 'customer_product_list.html')

# products1/viewsets.py
# products1/viewsets.py

from rest_framework import viewsets, filters, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from django.views.generic import TemplateView
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import (
    Product, ProductType, ProductModel, BillingUnit, MeasurementUnit,
    AttributeDefinition, ProductVariant, ProductImage, VariantImage
)
from .serializers import (
    ProductSerializer, ProductTypeSerializer, ProductModelSerializer,
    BillingUnitSerializer, MeasurementUnitSerializer,
    AttributeDefinitionSerializer, ProductVariantSerializer,
    VariantImageSerializer
)

# --- Master Data ViewSets (no changes here) ---
class ProductTypeViewSet(viewsets.ModelViewSet):
    queryset = ProductType.objects.all()
    serializer_class = ProductTypeSerializer

class ProductModelViewSet(viewsets.ModelViewSet):
    queryset = ProductModel.objects.select_related('type')
    serializer_class = ProductModelSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type']

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
    filterset_fields = ['field_type', 'name']
    search_fields = ['name']


# --- Product ViewSet ---
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.prefetch_related('variants', 'images')
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['type', 'is_active']
    search_fields = ['name', 'sku', 'type__name', 'model__name']
    parser_classes = [MultiPartParser, FormParser, JSONParser] # Keep these on the class

    # Add swagger_auto_schema for create method to explicitly use JSON
    @swagger_auto_schema(
        request_body=ProductSerializer, # Use the serializer for JSON body
        consumes=['application/json', 'multipart/form-data'], # Indicate it can consume both
        # Here's the key: if you truly want to support nested images via multipart,
        # drf-yasg doesn't represent it nicely. You might need a separate serializer
        # or manual_parameters here if this specific POST needs form data and files.
        # For now, let's assume the main serializer is primarily for JSON,
        # and the @action takes care of bulk image uploads.
        # If you want to enable complex multipart, you'd define manual_parameters here too,
        # which would require a flat structure for images (e.g., 'image_0', 'is_primary_0').
    )
    def create(self, request, *args, **kwargs):
        # Override create to ensure serializer handles potential multipart data if needed
        # This part doesn't change from standard DRF, as serializer.is_valid() handles parsing.
        return super().create(request, *args, **kwargs)

    # Add swagger_auto_schema for update method to explicitly use JSON
    @swagger_auto_schema(
        request_body=ProductSerializer, # Use the serializer for JSON body
        consumes=['application/json', 'multipart/form-data'], # Indicate it can consume both
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Upload multiple images for a specific product via direct file upload. "
                              "For nested image handling in create/update, use the main POST/PUT methods.",
        manual_parameters=[
            openapi.Parameter(
                name='images',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_FILE),
                required=True,
                description='List of image files to upload for the product'
            ),
        ],
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Images uploaded successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'status': openapi.Schema(type=openapi.TYPE_STRING)}
                )
            ),
            status.HTTP_400_BAD_REQUEST: "Bad Request"
        }
    )
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser], url_path='upload-images')
    def upload_images(self, request, pk=None):
        product = self.get_object()
        for file in request.FILES.getlist('images'):
            ProductImage.objects.create(product=product, image=file)
        return Response({'status': 'images uploaded'}, status=status.HTTP_201_CREATED)


class VariantImageViewSet(viewsets.ModelViewSet):
    queryset = VariantImage.objects.all()
    serializer_class = VariantImageSerializer

    @swagger_auto_schema(operation_description="Upload a variant image", request_body=VariantImageSerializer)
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


# --- Product Variant ViewSet ---
class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.select_related(
        'product', 'measurement_unit', 'billing_unit'
    ).prefetch_related('attributes__attribute', 'images')
    serializer_class = ProductVariantSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    # Add swagger_auto_schema for create method to explicitly use JSON
    @swagger_auto_schema(
        request_body=ProductVariantSerializer,
        consumes=['application/json', 'multipart/form-data'],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    # Add swagger_auto_schema for update method to explicitly use JSON
    @swagger_auto_schema(
        request_body=ProductVariantSerializer,
        consumes=['application/json', 'multipart/form-data'],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Upload multiple images for a specific product variant via direct file upload. "
                              "For nested image handling in create/update, use the main POST/PUT methods.",
        manual_parameters=[
            openapi.Parameter(
                name='images',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_FILE),
                required=True,
                description='List of image files to upload for the variant'
            ),
        ],
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Variant images uploaded successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'status': openapi.Schema(type=openapi.TYPE_STRING)}
                )
            ),
            status.HTTP_400_BAD_REQUEST: "Bad Request"
        }
    )
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser], url_path='upload-images')
    def upload_images(self, request, pk=None):
        variant = self.get_object()
        for file in request.FILES.getlist('images'):
            VariantImage.objects.create(variant=variant, image=file)
        return Response({'status': 'variant images uploaded'}, status=status.HTTP_201_CREATED)


# --- Frontend SPA and Admin View ---

class ProductSPAView(TemplateView):
    template_name = "products/index.html"

#@staff_member_required
def master_admin_view(request):
    return render(request, 'admin_master.html')

def customer_product_list(request):
    return render(request, 'customer_product_list.html')