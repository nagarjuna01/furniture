from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views 
from .views import part_evaluation_test

# --- Router Setup ---
# We use one router for all API endpoints, as they all fall under one architecture.
router = DefaultRouter()

# 1. Product Hierarchy Endpoints (Full CRUD via ModelViewSet)
# Maps to: /api/product-categories/
router.register(r'product-categories', views.ModularProductCategoryViewSet, basename='product-category')
# Maps to: /api/product-types/
router.register(r'product-types', views.ModularProductTypeViewSet, basename='product-type')
# Maps to: /api/product-models/
router.register(r'product-models', views.ModularProductModelViewSet, basename='product-model')

# 🔑 Core CRUD Endpoint for the main product configuration
# Maps to: /api/products/
router.register(r'products', views.ModularProductViewSet, basename='modular-product')

# 2. Source Data Endpoints (for filter lookups)
# Maps to: /api/materials/
router.register(r'materials', views.WoodEnFilterViewSet, basename='wooden-filter')
# Maps to: /api/edgebands/
router.register(r'edgebands', views.EdgeBandFilterViewSet, basename='edgeband-filter')
# Maps to: /api/hardware/
router.register(r'hardware', views.HardwareFilterViewSet, basename='hardware-filter')


# --- URL Patterns ---
urlpatterns = [
    # ----------------------------------------------------
    # API ENDPOINTS 
    # ----------------------------------------------------
    
    # All router registrations are included under the 'api/' path
    path('api/', include(router.urls)),

    # ----------------------------------------------------
    # UI/FRONTEND VIEW
    # ----------------------------------------------------
    
    # Paths to serve the main configuration UI
    path('ui/', views.modular_config_ui, name='configurator_ui'),
    path('uicopy/', views.modular_config_ui_copy, name='configurator_ui_copy'),
    path('mproduct/',views.layout_design,name='layout design'),
    path('addproduct/',views.add_product,name='add_product'),
    path('part-evaluation/<int:product_id>/', part_evaluation_test, name='part-evaluation-test'),
]