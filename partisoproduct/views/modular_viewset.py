from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from partisoproduct.models import Modular1, Constraint, HardwareRule
from partisoproduct.serializers import (
    Modular1Serializer, ConstraintSerializer, HardwareRuleSerializer
)


class ConstraintViewSet(viewsets.ModelViewSet):
    queryset = Constraint.objects.all()
    serializer_class = ConstraintSerializer
    # permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name', 'abbreviation', 'modular_product']  # ✅ Added here
    search_fields = ['name', 'abbreviation']
    ordering_fields = ['name', 'value']


class HardwareRuleViewSet(viewsets.ModelViewSet):
    queryset = HardwareRule.objects.all()
    serializer_class = HardwareRuleSerializer
    # permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name', 'is_custom', 'modular_product']  # ✅ Add this
    search_fields = ['name', 'equation']
    ordering_fields = ['name', 'is_custom']



class Modular1ViewSet(viewsets.ModelViewSet):
    queryset = Modular1.objects.prefetch_related('product_parameters', 'hardware_rules').all()
    serializer_class = Modular1Serializer
    #permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['name', 'uuid']
    ordering_fields = ['created_at', 'updated_at']
