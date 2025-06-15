# orders/urls.py or customers/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet,CustomerRegisterView

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)

urlpatterns = [
    path('register/', CustomerRegisterView.as_view(), name='customer_register'),
    path('', include(router.urls)),
]
