# furniture/urls.py
from django.contrib import admin
from django.urls import path, include
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
    path('orders/', include('order.urls')),  # Ensure the path matches the app name
    #path('products/', include('products.urls')),  # Product app URL routing
    path('customers/', include('customer.urls')),  # Customers URLs
    path('pmodular/', include('pmodular.urls')),  # Customers URLs
    #path('cart/', include('cart.urls')),
   
    path('payment/', include('payment.urls')),  # Include payment URLs
    path('material/', include('material.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # Add this line
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-docs'),  # Correct this line

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
