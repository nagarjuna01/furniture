# products/urls.py (remains as before)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import viewsets, views

# Create a router for DRF ViewSets
router = DefaultRouter()
router.register(r'product-categories', viewsets.ProductCategoryViewSet)
router.register(r'types', viewsets.TypeViewSet)
router.register(r'models', viewsets.ModelViewSet)
router.register(r'units', viewsets.UnitViewSet)
router.register(r'parts', viewsets.PartViewSet)
router.register(r'modules', viewsets.ModuleViewSet)
router.register(r'coupons', viewsets.CouponViewSet)
router.register(r'reviews', viewsets.ReviewViewSet)

# Register polymorphic product viewset
router.register(r'products', viewsets.ProductViewSet)

# If you need separate API endpoints for specific product types:
router.register(r'standard-products', viewsets.StandardProductViewSet)
router.register(r'custom-products', viewsets.CustomProductViewSet)
router.register(r'modular-products', viewsets.ModularProductViewSet)


# --- New Router Registrations for Layout/Rooms (Commented for future use) ---
# router.register(r'buildings', views.BuildingViewSet)
# router.register(r'floors', views.FloorViewSet)
# router.register(r'rooms', views.RoomViewSet)

app_name = 'products'

urlpatterns = [
    # --- API Endpoints ---
    path('v1/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')), # For DRF login/logout

    # # --- Frontend Views ---
    # path('', views.HomeView.as_view(), name='home'),
    path('catalog/', views.product_list_view, name='product_list'), # Changed
    path('catalog/<slug:slug>/', views.product_detail_view, name='product_detail'), # Changed
    path('configurator/<int:pk>/', views.modular_product_configurator, name='modular_product_configurator'),
    path('admin-custom/modular-products/', views.modular_product_admin_list, name='custom-admin-modular-product-list'),
    path('admin-custom/modular-products/<int:pk>/configurator/', views.modular_product_admin_configurator, name='custom-admin-modular-product-configurator'),

]