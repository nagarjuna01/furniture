from rest_framework_nested import routers
from django.urls import path, include
from .views import (
    ModularProductViewSet, PartTemplateViewSet,
    PartMaterialWhitelistViewSet, PartEdgeBandWhitelistViewSet,
    PartHardwareRuleViewSet, modular
)

# Main router
router = routers.DefaultRouter()
router.register(r"products", ModularProductViewSet, basename="products")

# Nested router for parts under products
products_router = routers.NestedDefaultRouter(router, r"products", lookup="product")
products_router.register(
    r"parts",
    PartTemplateViewSet,
    basename="product-parts"
)

# Other isolated resources
router.register(r"part-materials", PartMaterialWhitelistViewSet, basename="part-materials")
router.register(r"part-edgebands", PartEdgeBandWhitelistViewSet, basename="part-edgebands")
router.register(r"part-hardware", PartHardwareRuleViewSet, basename="part-hardware")

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/", include(products_router.urls)),
    path("modular/", modular, name="modular_page"),
]
