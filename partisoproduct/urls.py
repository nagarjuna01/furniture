from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views.quote_viewset import MvpQuoteRequestViewSet
from .views.part_viewset import Part1ViewSet
from .views.modular_viewset import ConstraintViewSet, HardwareRuleViewSet, Modular1ViewSet
from .views.djangoviews import modular_products_list,create_quote_page

router = DefaultRouter()
router.register(r'parts', Part1ViewSet, basename='part1')
router.register(r'quotes', MvpQuoteRequestViewSet)
router.register(r'constraints', ConstraintViewSet)
router.register(r'hardware-rules', HardwareRuleViewSet)
router.register(r'modular1', Modular1ViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('modular-products/', modular_products_list, name='modular_products_list'),
    path('create-quote/', create_quote_page, name='create_quote_page'),
    
]
