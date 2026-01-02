from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductTypeViewSet,ProductImageViewSet,VariantImageViewSet,ProductSeriesViewSet,ProductViewSet,ProductVariantViewSet,AttributeDefinitionViewSet,master_admin_view,customer_product_list,product_management_view,VariantAttributeValueViewSet

router = DefaultRouter()

router.register("product-types", ProductTypeViewSet, basename="product-type")
router.register("product-series", ProductSeriesViewSet, basename="product-series")
router.register("products", ProductViewSet, basename="product")
router.register("product-variants", ProductVariantViewSet, basename="product-variant")
router.register("attributes", AttributeDefinitionViewSet, basename="attribute")
router.register("product-images", ProductImageViewSet, basename="product-image")
router.register("variant-images", VariantImageViewSet, basename="variant-image")
router.register("variant-attributes", VariantAttributeValueViewSet)

urlpatterns = [
    # ---------------- API ----------------
    path("v1/", include(router.urls)),
   
    # ------------- Admin / Internal ------
    path("admin/master/", master_admin_view, name="master-admin"),
    path("sp/",product_management_view,name= "product-management"),

    # ------------- Customer View ---------
    path("products/view/", customer_product_list, name="customer-product-list"),
]
