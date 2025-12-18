from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ProductTypeViewSet,
    ProductSeriesViewSet,
    BillingUnitViewSet,
    MeasurementUnitViewSet,
    AttributeDefinitionViewSet,
    ProductViewSet,
    ProductVariantViewSet,
    ProductSPAView,
    master_admin_view,
    customer_product_list,
)

router = DefaultRouter()

# ------------------------------------------------------------------
# MASTER DATA
# ------------------------------------------------------------------
router.register(r"product-types", ProductTypeViewSet, basename="product-type")
router.register(r"product-series", ProductSeriesViewSet, basename="product-series")
router.register(r"billing-units", BillingUnitViewSet, basename="billing-unit")
router.register(r"measurement-units", MeasurementUnitViewSet, basename="measurement-unit")
router.register(r"attributes", AttributeDefinitionViewSet, basename="attribute-definition")

# ------------------------------------------------------------------
# CORE INVENTORY
# ------------------------------------------------------------------
router.register(r"products", ProductViewSet, basename="product")
router.register(r"variants", ProductVariantViewSet, basename="product-variant")

urlpatterns = [
    # ---------------- API ----------------
    path("api/", include(router.urls)),

    # ------------- Frontend SPA ----------
    path("user/", ProductSPAView.as_view(), name="product_spa"),

    # ------------- Admin / Internal ------
    path("admin/master/", master_admin_view, name="master-admin"),

    # ------------- Customer View ---------
    path("products/view/", customer_product_list, name="customer-product-list"),
]
