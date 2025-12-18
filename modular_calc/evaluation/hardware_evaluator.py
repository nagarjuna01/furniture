from typing import Dict
from .evaluator import ExpressionEvaluator
from .context import ProductContext, to_decimal
from decimal import Decimal

class HardwareEvaluator:
    """Evaluate hardware quantity per part or product."""

    def __init__(self, hardware_rule, context: Dict[str, Decimal]):
        self.hardware_rule = hardware_rule
        self.evaluator = ExpressionEvaluator(context)

    def evaluate(self) -> Dict[str, Decimal] | None:
        # Check applicability condition
        if getattr(self.hardware_rule, "applicability_condition", None):
            if not self.evaluator.eval(self.hardware_rule.applicability_condition):
                return None  # skip

        qty = self.evaluator.eval(self.hardware_rule.quantity_equation)
        return {
            "hardware": self.hardware_rule.hardware.name,
            "quantity": to_decimal(qty)
        }
