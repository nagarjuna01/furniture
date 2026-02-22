from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsQuoteEditable(BasePermission):
    """
    Blocks write operations if quote is locked
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.status != "locked"


from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from accounts.models import GlobalVariable
from modular_calc.evaluation.product_engine import ProductEngine
from quoting.models import QuotePart, QuotePartHardware

# quoting/services.py alignment

class QuoteProductService:

    @staticmethod
    def build_context(qp):
        ctx = {
            "product_length": float(qp.length_mm),
            "product_width": float(qp.width_mm),
            "product_height": float(qp.height_mm),
            "quantity": qp.quantity,
        }
        # Fetch global variables for the specific factory (tenant)
        globals_map = {
            v.abbr: float(v.value)
            for v in GlobalVariable.objects.filter(tenant=qp.tenant)
        }
        ctx.update(globals_map)
        ctx.update(qp.config_parameters or {})
        return ctx

    @staticmethod
    def evaluate(qp):
        context = QuoteProductService.build_context(qp)
        # ALIGNMENT: ProductEngine.__init__ needs (product, dims, params) 
        engine = ProductEngine(qp.product_template, context, context)
        # The engine's 'run' method triggers the multi-quantity logic [cite: 98]
        return engine.run()

    @staticmethod
    @transaction.atomic
    def expand_to_parts(qp):
        # FIX: Access quote status through the solution bridge 
        if qp.solution.quote.status == "locked":
            raise ValidationError("Quote is locked")

        # Run the aligned engine
        results = QuoteProductService.evaluate(qp)
        
        # ProductEngine returns quotes mapped by quantity 
        qty_str = str(qp.quantity)
        evaluation = results.get("quotes", {}).get(qty_str, {}).get("bom", {})

        total_cp = Decimal("0.00")
        total_sp = Decimal("0.00")

        qp.parts.all().delete()

        # Iterate through the engine's BOM parts 
        for part in evaluation.get("parts", []):
            qp_part = QuotePart.objects.create(
                tenant=qp.tenant,
                quote_product=qp,
                part_template=part.get("template_obj"),
                part_name=part["name"],
                length_mm=part["length"],
                width_mm=part["width"],
                thickness_mm=part.get("thickness", 0),
                part_qty=part["quantity"],
                material=part.get("material_obj"),
                total_part_cp=part.get("total_cp", 0),
                total_part_sp=part.get("total_sp", 0)
            )
            total_cp += Decimal(str(qp_part.total_part_cp))
            total_sp += Decimal(str(qp_part.total_part_sp))

        # Save the 1,045.00 total to the Product level [cite: 111, 112]
        qp.total_cp = total_cp
        qp.total_sp = total_sp
        qp.validated = True
        qp.save(update_fields=["total_cp", "total_sp", "validated"])

        # Trigger global recalculation
        from quoting.services.recalculation import recalc_quote
        recalc_quote(qp.solution.quote)
        return qp

# quoting/services/recalculation.py

from django.db.models import Sum

def recalc_quote_product(qp):
    totals = qp.parts.aggregate(
        cp=Sum("total_part_cp"),
        sp=Sum("total_part_sp"),
    )

    qp.total_cp = totals["cp"] or 0
    qp.total_sp = totals["sp"] or 0
    qp.validated = True
    qp.save(update_fields=["total_cp", "total_sp", "validated"])


def recalc_quote_solution(solution):
    totals = solution.products.aggregate(
        cp=Sum("total_cp"),
        sp=Sum("total_sp"),
    )

    solution.total_cp = totals["cp"] or 0
    solution.total_sp = totals["sp"] or 0
    solution.save(update_fields=["total_cp", "total_sp"])


def recalc_quote(quote):
    totals = quote.solutions.aggregate(
        cp=Sum("total_cp"),
        sp=Sum("total_sp"),
    )

    quote.total_cp = totals["cp"] or 0
    quote.total_sp = totals["sp"] or 0
    quote.save(update_fields=["total_cp", "total_sp"])
