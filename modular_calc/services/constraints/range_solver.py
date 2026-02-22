import logging
from decimal import Decimal
from modular_calc.evaluation.evaluator import ExpressionEvaluator

logger = logging.getLogger(__name__)

def solve_ranges(constraints, target_var, context):
    min_val = Decimal("-Infinity")
    max_val = Decimal("Infinity")

    evaluator = ExpressionEvaluator(context)

    for c in constraints:
        if c["lhs"] != target_var:
            continue

        try:
            rhs_val = evaluator.eval(c["rhs"])
        except Exception as e:
            logger.warning("Constraint skipped: %s", e)
            continue

        val = Decimal(str(rhs_val))

        if c["op"] in ("Gt", "GtE"):
            min_val = max(min_val, val)
        elif c["op"] in ("Lt", "LtE"):
            max_val = min(max_val, val)

    return {"min": min_val, "max": max_val}
