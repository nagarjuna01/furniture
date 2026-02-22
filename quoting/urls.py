from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import ModularCalculateView
# Keep all your existing viewset imports
from .viewsets import (
    QuoteRequestViewSet, QuoteProductViewSet, MarketplaceCatalogViewSet,
    MarketplaceQuoteViewSet, QuotePartHardwareViewSet, QuotePartViewSet,
    OverrideLogViewSet, QuoteRevisionViewSet, QuoteCommunicationViewSet,QuoteSolutionViewSet
)
from quoting.visuals.views import product_svg

app_name = 'quoting'

# 1. Existing DRF router for CRUD operations
router = DefaultRouter()
router.register(r"marketplace-catalog", MarketplaceCatalogViewSet, basename="marketplace-catalog")
router.register(r"marketplace-quotes", MarketplaceQuoteViewSet, basename="marketplace-quotes")
router.register(r"quotes", QuoteRequestViewSet, basename="quote-request")
router.register(r"solutions", QuoteSolutionViewSet, basename="quote-solution")
router.register(r"quote-products", QuoteProductViewSet, basename="quote-product")
router.register(r"quote-parts", QuotePartViewSet, basename="quote-part")
router.register(r"quote-hardware", QuotePartHardwareViewSet, basename="quote-part-hardware")
router.register(r"quote-overrides", OverrideLogViewSet, basename="override-log")
router.register(r"quote-communications", QuoteCommunicationViewSet, basename="quote-communication")
router.register(r"quote-revisions", QuoteRevisionViewSet, basename="quote-revision")

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/", include("quoting.api.urls")),
    path("pipeline/", views.quote_list_view, name="quote_list"),
    path("workspace/<int:quote_id>/", views.quote_workspace_view, name="quote_workspace"),
    path("api/visuals/product/<int:quote_product_id>/svg/", product_svg, name="product-svg"),
    path('', views.quote_list_view, name='quote_list_root'),
    path('api/modular/calculate/', ModularCalculateView.as_view(), name='modular-calc'),
    # path("quotes/<int:quote_id>/", views.quote_detail_view, name="quote-detail"), # Note: int vs uuid conflict check
]