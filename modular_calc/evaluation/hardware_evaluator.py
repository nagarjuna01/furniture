#modular_calc/evaluation/hardware_evaluator.py
from typing import Dict
from .evaluator import ExpressionEvaluator
from .context import ProductContext, to_decimal
from decimal import Decimal

class HardwareEvaluator:
    """Evaluate hardware quantity per part or product using MAX logic."""

    def __init__(self, hardware_rule, context: Dict[str, Decimal]):
        self.hardware_rule = hardware_rule
        self.evaluator = ExpressionEvaluator(context)

    def evaluate(self) -> Dict[str, Decimal] | None:
        base_qty = self.evaluator.eval(self.hardware_rule.quantity_equation) or 0
        
        condition_val = 0
        if getattr(self.hardware_rule, "applicability_condition", None):
            condition_val = self.evaluator.eval(self.hardware_rule.applicability_condition) or 0

        final_qty = max(to_decimal(base_qty), to_decimal(condition_val))
        if final_qty <= 0:
            return None
        return {
            "hardware": self.hardware_rule.hardware.h_name,
            "quantity": final_qty,
            "hardware_obj": self.hardware_rule.hardware
        }
