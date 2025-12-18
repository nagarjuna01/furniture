from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from .serializers import ProductEvaluationSerializer
from .product_engine import ProductEngine
from products.models import ModularProduct

class ProductEvaluationViewSet(viewsets.ViewSet):
    """
    Evaluate a product BOM, cutlist, and pricing.
    Endpoint: /api/evaluate/products/<pk>/run/
    """

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        product = get_object_or_404(ModularProduct, pk=pk)

        product_dims = request.data.get('product_dims', {})
        parameters = request.data.get('parameters', {})
        quantities = request.data.get('quantities', [1])

        engine = ProductEngine(product, product_dims, parameters, quantities)
        result = engine.run()

        serializer = ProductEvaluationSerializer(result)
        return Response(serializer.data, status=status.HTTP_200_OK)
