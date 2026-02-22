from django.db.models import Sum
from decimal import Decimal

def recalc_quote_product(qp):
    # 1. Update each Part's total first (Material + its own Hardware)
    for part in qp.parts.all():
        hw_totals = part.hardware.aggregate(sp=Sum("total_sp"), cp=Sum("total_cp"))
        # We assume material cost is already in total_part_sp from the Service Layer
        # If not, add material calculation logic here
        part.save() # Ensure part is fresh

    # 2. Now sum the "Complete" parts
    part_totals = qp.parts.aggregate(
        cp=Sum("total_part_cp"),
        sp=Sum("total_part_sp"),
    )

    total_cp = (part_totals["cp"] or 0)
    total_sp = (part_totals["sp"] or 0)

    # 3. Apply Adjustment (e.g., Waste Factor or Profit Margin)
    factor = getattr(qp, 'adjustment_factor', Decimal('1.00'))
    qp.total_cp = Decimal(total_cp) * factor
    qp.total_sp = Decimal(total_sp) * factor
    
    qp.validated = True
    qp.save(update_fields=["total_cp", "total_sp", "validated"])
    return qp

def recalc_quote_solution(solution):
    """
    Step 2: Aggregates all products in a room/solution.
    Required to fix the ImportError in your Serializer.
    """
    totals = solution.products.aggregate(
        cp=Sum("total_cp"),
        sp=Sum("total_sp"),
    )
    solution.total_cp = totals["cp"] or Decimal("0.00")
    solution.total_sp = totals["sp"] or Decimal("0.00")
    solution.save(update_fields=["total_cp", "total_sp"])
    return solution

def recalc_quote(quote):
    """
    Step 3: Grand Total (Standard + Modular).
    """
    standard = quote.items.aggregate(sp=Sum("line_total_sp"), cp=Sum("line_total_cp"))
    modular = quote.solutions.aggregate(sp=Sum("total_sp"), cp=Sum("total_cp"))

    quote.total_sp = (standard["sp"] or Decimal("0.00")) + (modular["sp"] or Decimal("0.00"))
    quote.total_cp = (standard["cp"] or Decimal("0.00")) + (modular["cp"] or Decimal("0.00"))
    
    quote.save(update_fields=["total_sp", "total_cp"])
    return quote