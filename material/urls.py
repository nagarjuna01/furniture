from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views



router = DefaultRouter()

# Register API viewsets
router.register(r'brands', views.BrandViewSet)
router.register(r'categories', views.CategoryViewSet)
router.register(r'category-types', views.CategoryTypesViewSet)
router.register(r'category-models', views.CategoryModelViewSet)
router.register(r'edgebands', views.EdgeBandViewSet)
router.register(r'woodens', views.WoodEnViewSet, basename='wooden')
router.register(r'hardware-groups', views.HardwareGroupViewSet)
router.register(r'hardware', views.HardwareViewSet)
router.register(r'edgeband-names', views.EdgebandNameViewSet, basename='edgebandname')


urlpatterns = [
    # API routes
    path('v1/', include(router.urls)),
    
    # Regular Django template views
    path('brand/', views.brand_list_page, name='brand_page'),
    path('category-browser/', views.category_browser, name='category-browser'),
    path('categories1/', views.category_list1, name='category-list1'),
    path('category-type/', views.category_types, name='category-types'),
    path('category-type/<int:category_id>/', views.category_type_list, name='category-type-list'),
    path('category-models/<int:category_type_id>/', views.category_models, name='category-models'),
    path('hardware-inventory/', views.hardware_view, name='hardware-inventory'),
    
    path('wooden-products/', views.wooden_products, name='wooden-products'),
    path('edgebands-page/', views.edgeband_list, name='edgeband-list-page'),

    # JSON filter endpoint example
    path('filter-categories/', views.filter_categories_by_select, name='filter-categories'),
]
