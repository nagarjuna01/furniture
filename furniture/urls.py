# furniture/urls.py
from django.contrib import admin
from django.urls import path, include, re_path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.conf import settings
from django.conf.urls.static import static

# Schema view for Swagger UI
schema_view = get_schema_view(
    openapi.Info(
        title="Furniture API",
        default_version='v1',
        description="API documentation for the Furniture E-Commerce platform",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@furniture.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    #path('orders/', include('order.urls')),  # Ensure the path matches the app name
    #path('products/', include('products.urls')),  # Product app URL routing
    path('products1/', include('products1.urls')),  # Product app URL routing
    path('customers/', include('customer.urls')),  # Customers URLs
    path('accounts/',include('accounts.urls')),
    path('partiso/', include('partisoproduct.urls')),  # partisoproduct URLs
    path('modularcalc/', include('modular_calc.urls')),  # Modular_calc URLs
    path('quoting/', include('quoting.urls')),  # quoting URLs
    #path('standprod/',include('standprod.urls')),
    
    #path('cart/', include('cart.urls')),
   
    #path('payment/', include('payment.urls')),  # Include payment URLs
    path('material/', include('material.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # Add this line
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-docs'),  # Correct this line
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
