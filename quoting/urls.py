from django.urls import path, include
from rest_framework.routers import DefaultRouter
from quoting.views import QuoteRequestViewSet, QuoteProductViewSet, QuotePartViewSet
from quoting.visuals.views import product_svg

router = DefaultRouter()
router.register(r"quotes", QuoteRequestViewSet, basename="quotes")
router.register(r"quote-products", QuoteProductViewSet, basename="quote-products")
router.register(r"quote-parts", QuotePartViewSet, basename="quote-parts")

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/visuals/product/<int:quote_product_id>/svg/", product_svg, name="product-svg"),
]
