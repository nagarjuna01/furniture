from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductTypeViewSet, ProductModelViewSet, BillingUnitViewSet,
    MeasurementUnitViewSet, AttributeDefinitionViewSet,
    ProductViewSet, ProductVariantViewSet,
    ProductSPAView, master_admin_view, VariantImageViewSet, customer_product_list
)

router = DefaultRouter()
router.register(r'types', ProductTypeViewSet, basename='product-type')
router.register(r'models', ProductModelViewSet, basename='product-model')
router.register(r'billing-units', BillingUnitViewSet, basename='billing-unit')
router.register(r'measurement-units', MeasurementUnitViewSet, basename='measurement-unit')
router.register(r'attributes', AttributeDefinitionViewSet, basename='attribute-definition')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'variants', ProductVariantViewSet, basename='product-variant')
router.register(r'variant-images', VariantImageViewSet, basename='variant-images')

urlpatterns = [
    path('api/', include(router.urls)),

    # Frontend SPA (for React/Vue/jQuery interface)
    path('user/', ProductSPAView.as_view(), name='product_spa'),

    # Admin dashboard
    path('admin/master/', master_admin_view, name='master-admin'),
    path('product_view/', customer_product_list, name='customer_product_list'),
]
