from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import subscription_expired,master_admin,material_login,material_logout,ConvertAPIView
from .viewsets import (
    ProductViewSet,
    ProductVariantViewSet,
    ProductTypeViewSet,
    ProductModelViewSet,
    ProductImageViewSet,
    VariantImageViewSet,
    AttributeDefinitionViewSet,
    VariantAttributeValueViewSet,
    DiscountViewSet,
    SupplierViewSet,
    WorkOrderViewSet,
    ShippingMethodViewSet,
    ShipmentViewSet,
    ProductReviewViewSet,
    MeasurementUnitViewSet,
    BillingUnitViewSet,
    
)

router = DefaultRouter()

# -------------------------------------------------
# PRODUCT CORE
# -------------------------------------------------
router.register(r'products', ProductViewSet, basename='products')
router.register(r'variants', ProductVariantViewSet, basename='variants')
router.register(r'product-types', ProductTypeViewSet, basename='product-types')
router.register(r'product-models', ProductModelViewSet, basename='product-models')

# -------------------------------------------------
# ATTRIBUTES SYSTEM
# -------------------------------------------------
router.register(r'attribute-definitions', AttributeDefinitionViewSet, basename='attribute-definitions')
router.register(r'variant-attributes', VariantAttributeValueViewSet, basename='variant-attributes')

# -------------------------------------------------
# MEDIA
# -------------------------------------------------
router.register(r'product-images', ProductImageViewSet, basename='product-images')
router.register(r'variant-images', VariantImageViewSet, basename='variant-images')

# -------------------------------------------------
# BUSINESS MODULES
# -------------------------------------------------
router.register(r'discounts', DiscountViewSet, basename='discounts')
router.register(r'suppliers', SupplierViewSet, basename='suppliers')
router.register(r'work-orders', WorkOrderViewSet, basename='work-orders')
router.register(r'shipping-methods', ShippingMethodViewSet, basename='shipping-methods')
router.register(r'shipments', ShipmentViewSet, basename='shipments')
router.register(r'reviews', ProductReviewViewSet, basename='reviews')
router.register(r'measurement-units', MeasurementUnitViewSet, basename='measurement-units')
router.register(r'billing-units', BillingUnitViewSet, basename='billingunit')

urlpatterns = [
    path('api/v1/', include(router.urls)),
    path("material-login/", material_login, name="material-login"),
    path("logout/", material_logout, name="material-logout"),
    path("subscription-expired/", subscription_expired, name="subscription_expired"),
    path("master-admin/", master_admin, name="master-admin"),
    path("convert/", ConvertAPIView.as_view(), name="unit-convert"),

]
