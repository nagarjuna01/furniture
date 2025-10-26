from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views 

# --- Router Setup ---
# We use one router for all API endpoints, as they all fall under one architecture.
router = DefaultRouter()

# 🔑 Core CRUD Endpoint
router.register(r'products', views.ModularProductViewSet, basename='modular-product')

# ----------------------------------------------------------------------------------
# SOURCE DATA ENDPOINTS (Modified/Added to directly match the requested frontend paths)
# ----------------------------------------------------------------------------------

# 1. FIX: Register WoodEnFilterViewSet under 'materials/'
# This resolves the 404 for GET /modularcalc/api/materials/
router.register(r'materials', views.WoodEnFilterViewSet, basename='wooden-filter')

# 2. FIX: Register EdgeBandFilterViewSet under 'edgebands/'
# This resolves the 404 for GET /modularcalc/api/edgebands/
router.register(r'edgebands', views.EdgeBandFilterViewSet, basename='edgeband-filter')

# 3. NEW: Register HardwareFilterViewSet under 'hardware/'
# This resolves the 404 for GET /modularcalc/api/hardware/
router.register(r'hardware', views.HardwareFilterViewSet, basename='hardware-filter')


# --- URL Patterns ---
urlpatterns = [
    # ----------------------------------------------------
    # API ENDPOINTS 
    # ----------------------------------------------------
    
    # The 'api/' prefix is defined here, which maps the router registers above:
    # e.g., 'api/' + 'materials' -> /api/materials/
    path('api/', include(router.urls)),

    # ----------------------------------------------------
    # UI/FRONTEND VIEW
    # ----------------------------------------------------
    
    # Path to serve the main configuration UI
    path('ui/', views.modular_config_ui, name='configurator_ui'),
]
