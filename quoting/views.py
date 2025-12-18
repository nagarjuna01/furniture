from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse

from .models import QuoteRequest, QuoteProduct, QuotePart, OverrideLog
from .serializers import QuoteRequestSerializer, QuoteProductSerializer, QuotePartSerializer
from modular_calc.evaluation.part_evaluator import PartEvaluator
from material.models.wood import WoodMaterial

from .visuals.services import render_svg


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
        product_dims = {
            "product_length": qp.length_mm,
            "product_width": qp.width_mm,
            "product_height": qp.height_mm,
        }
        valid = True
        for pt in qp.product_template.part_templates.all():
            evaluator = PartEvaluator(pt, product_dims, parameters={})
            result = evaluator.evaluate()
            if result["length"] <= 0 or result["width"] <= 0 or result["quantity"] <= 0:
                valid = False
                break

        qp.validated = valid
        qp.save(update_fields=["validated"])
        return Response({"validated": valid})

    @action(detail=True, methods=["post"])
    def expand_parts(self, request, pk=None):
        qp = self.get_object()
        if not qp.validated:
            return Response({"detail": "Product not validated."}, status=status.HTTP_400_BAD_REQUEST)

        # Clear previous parts
        qp.parts.all().delete()

        product_dims = {
            "product_length": qp.length_mm,
            "product_width": qp.width_mm,
            "product_height": qp.height_mm,
        }

        count = 0
        for pt in qp.product_template.part_templates.all():
            evaluator = PartEvaluator(pt, product_dims, parameters={})
            part_data = evaluator.evaluate()

            qp_part = QuotePart.objects.create(
                quote_product=qp,
                part_template=pt,
                part_name=part_data["name"],
                length_mm=part_data["length"],
                width_mm=part_data["width"],
                part_qty=int(part_data["quantity"]),
                thickness_mm=part_data["thickness"],
                shape_wastage_multiplier=part_data["shape_wastage_multiplier"],
                material=part_data["material_obj"],
                edgeband_top=part_data["edgeband_objs"].get("top"),
                edgeband_bottom=part_data["edgeband_objs"].get("bottom"),
                edgeband_left=part_data["edgeband_objs"].get("left"),
                edgeband_right=part_data["edgeband_objs"].get("right"),
            )
            count += 1

        parts = QuotePart.objects.filter(quote_product=qp)
        data = QuotePartSerializer(parts, many=True).data
        return Response({"created_parts": count, "parts": data}, status=status.HTTP_200_OK)


class QuotePartViewSet(viewsets.ModelViewSet):
    queryset = QuotePart.objects.select_related("quote_product", "part_template", "material")
    serializer_class = QuotePartSerializer

    @action(detail=True, methods=["post"])
    def override_material(self, request, pk=None):
        qp = self.get_object()
        old = qp.material
        new_id = request.data.get("material")
        reason = request.data.get("reason", "")

        if not new_id:
            return Response({"detail": "material required"}, status=400)

        new = WoodEn.objects.get(pk=new_id)

        # Warn if thickness mismatch
        warn = None
        if str(new.thickness_mm) != str(qp.thickness_mm):
            warn = f"Material thickness {new.thickness_mm} != part thickness {qp.thickness_mm}"

        qp.material = new
        qp.override_by_employee = True
        qp.override_reason = reason
        qp.save()

        OverrideLog.objects.create(
            quote_part=qp,
            field="material",
            old_value=str(old) if old else "",
            new_value=str(new),
            reason=reason,
            changed_by=request.user if request.user.is_authenticated else None
        )
        return Response({"ok": True, "warning": warn})
