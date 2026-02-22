# modular_cal/evaluation/urls.py
from rest_framework.routers import DefaultRouter
from .viewsets import ProductEvaluationViewSet

router = DefaultRouter()
router.register(r'products', ProductEvaluationViewSet, basename='product-evaluate')

urlpatterns = router.urls
