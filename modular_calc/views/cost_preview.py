# views/cost_preview.py
from rest_framework.views import APIView
from rest_framework.response import Response

from modular_calc.services.cost.bom_builder import build_bom


class CostPreviewView(APIView):

    def post(self, request):
        evaluated_parts = request.data.get("parts")
        hardware_rules = request.data.get("hardware_rules", [])

        bom = build_bom(evaluated_parts, hardware_rules)

        return Response(bom) 
