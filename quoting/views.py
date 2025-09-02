from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import QuoteRequest, QuoteProduct, QuotePart
from .serializers import QuoteRequestSerializer, QuoteProductSerializer, QuotePartSerializer


class QuoteRequestViewSet(viewsets.ModelViewSet):
    queryset = QuoteRequest.objects.all().prefetch_related("products")
    serializer_class = QuoteRequestSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user if self.request.user.is_authenticated else None)


class QuoteProductViewSet(viewsets.ModelViewSet):
    queryset = QuoteProduct.objects.select_related("product_template", "quote")
    serializer_class = QuoteProductSerializer

    @action(detail=True, methods=["post"])
    def validate_dimensions(self, request, pk=None):
        qp = self.get_object()
        ok = qp.validate_inputs()
        qp.save(update_fields=["validated"])
        return Response({"validated": ok})

    @action(detail=True, methods=["post"])
    def expand_parts(self, request, pk=None):
        qp = self.get_object()
        if not qp.validated and not qp.validate_inputs():
            return Response({"detail": "Dimensions invalid."}, status=status.HTTP_400_BAD_REQUEST)

        count = qp.expand_to_parts()
        parts = QuotePart.objects.filter(quote_product=qp)
        data = QuotePartSerializer(parts, many=True).data
        return Response({"created_parts": count, "parts": data}, status=status.HTTP_200_OK)


class QuotePartViewSet(viewsets.ModelViewSet):
    queryset = QuotePart.objects.select_related("quote_product", "part_template", "material")
    serializer_class = QuotePartSerializer

    @action(detail=True, methods=["post"])
    def override_material(self, request, pk=None):
        """
        Employee can change material; we log the override and warn if thickness mismatch.
        payload: { "material": <id>, "reason": "budget" }
        """
        qp = self.get_object()
        old = qp.material
        new_id = request.data.get("material")
        reason = request.data.get("reason", "")
        if not new_id:
            return Response({"detail": "material required"}, status=400)

        from material.models import Material
        new = Material.objects.get(pk=new_id)

        # warn if thickness mismatch
        warn = None
        if str(new.thickness_mm) != str(qp.thickness_mm):
            warn = f"Material thickness {new.thickness_mm} ≠ part thickness {qp.thickness_mm}"

        qp.material = new
        qp.override_by_employee = True
        qp.override_reason = reason
        qp.save()

        from .models import OverrideLog
        OverrideLog.objects.create(
            quote_part=qp,
            field="material",
            old_value=str(old) if old else "",
            new_value=str(new),
            reason=reason,
            changed_by=request.user if request.user.is_authenticated else None
        )
        return Response({"ok": True, "warning": warn})
