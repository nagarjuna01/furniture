# modular_calc/evaluation/viewsets.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
import logging

from .serializers import ProductEvaluationSerializer
from .product_engine import ProductEngine
from .payload_builder import ProductPayloadBuilder
from products.models import ModularProduct

logger = logging.getLogger(__name__)


class ProductEvaluationViewSet(viewsets.ViewSet):
    """
    Evaluate a product BOM, cutlist, and pricing.
    Endpoint: /api/evaluate/products/<pk>/run/
    """

    @action(detail=True, methods=["post"])
    def run(self, request, pk=None):
        qs = ModularProduct.objects.all()

        if not request.user.is_superuser:
            qs = qs.filter(tenant=request.user.tenant)

        product = get_object_or_404(qs, pk=pk)

        product_dims = request.data.get("product_dims", {})
        parameters = request.data.get("parameters", {})
        quantities = request.data.get("quantities", [1])

        try:
            payload = ProductPayloadBuilder(
                product=product,
                product_dims=product_dims,
                parameters=parameters,
                quantities=quantities,
            ).build()

            engine = ProductEngine(
                payload,
                stock_sheet_size=request.data.get("stock_sheet_size", 2440),
                sheet_price=request.data.get("sheet_price"),
            )

            result = engine.run()

            serializer = ProductEvaluationSerializer(result)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Product evaluation failed")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
