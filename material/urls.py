from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# -----------------------------
# API ViewSets
# -----------------------------
router.register(r'brands', views.BrandViewSet)
router.register('measurement-units', views.MeasurementUnitViewSet)
router.register('billing-units', views.BillingUnitViewSet)
router.register(r'categories', views.CategoryViewSet,basename="category")
router.register(r'category-types', views.CategoryTypesViewSet,basename="category-type")
router.register(r'category-models', views.CategoryModelViewSet, basename="category-model")
router.register(r'edgebands', views.EdgeBandViewSet)
router.register(r'woodens', views.WoodMaterialViewSet, basename='wooden')
router.register(r'hardware-groups', views.HardwareGroupViewSet)
router.register(r'hardware', views.HardwareViewSet,basename='hardware')
router.register(r'edgeband-names', views.EdgebandNameViewSet, basename='edgebandname')

# -----------------------------
# URL Patterns
# -----------------------------
urlpatterns = [
    # API v1 Root
    path('v1/', include(router.urls)),

    # -----------------------------
    # TEMPLATE ROUTES (HTML)
    # -----------------------------

    path('brand/', views.brand_list_page, name='brand_page'),
    path('category-browser/', views.category_browser, name='category-browser'),
    path('measurement-units/',views.measurement_unit_view,
        name="measurement-unit-ui",
    ),
    path('billing-units/',views.billing_unit_view,name="billing-unit-ui",),
    # # Category tree
    # #path('category-type/', views.category_types, name='category-types'),
    # #path('category-type/<int:category_id>/', views.category_type_list, name='category-type-list'),
    # #path('category-models/<int:category_type_id>/', views.category_models, name='category-models'),

    # # Hardware, Edgeband, Wooden
    path('hardware-inventory/', views.hardware_view, name='hardware-inventory'),
    path('edgebands-page/', views.edgeband_list, name='edgeband-list-page'),

    # JSON-only endpoint (Select Filter)
    #path('filter-categories/', views.filter_categories_by_select, name='filter-categories'),
]
