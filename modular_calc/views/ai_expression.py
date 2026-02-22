from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from modular_calc.evaluation.context import ProductContext
from modular_calc.services.ai.intent_parser import parse_intent
from modular_calc.services.ai.candidate_generator import generate_candidates
from modular_calc.services.ai.candidate_filter import filter_candidates
from modular_calc.services.ai.optimizer import optimize_candidates
from modular_calc.services.ai.explainer import explain_candidates


class AIExpressionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Input:
        {
          "intent": "apron must be shorter than product by 20mm",
          "product_id": 12
        }
        """

        intent_text = request.data.get("intent")
        product_id = request.data.get("product_id")

        if not intent_text or not product_id:
            return Response(
                {"error": "intent and product_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1️⃣ Build deterministic context
        ctx = ProductContext.from_product(product_id)
        context = ctx.get_context()

        # 2️⃣ Parse intent → structured meaning
        structured_intent = parse_intent(intent_text)

        # 3️⃣ Generate AI candidates (unsafe zone)
        raw_candidates = generate_candidates(structured_intent, ctx)

        # 4️⃣ Deterministic validation gate
        valid_candidates = filter_candidates(raw_candidates, context)

        if not valid_candidates:
            return Response(
                {"error": "No valid expressions could be generated"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 5️⃣ Optimize (optional, safe)
        optimized = optimize_candidates(valid_candidates, context)

        # 6️⃣ Explain results
        explained = explain_candidates(optimized)

        return Response(
            {"candidates": explained},
            status=status.HTTP_200_OK
        )
