# modular_calc/evaluation/validators.py
from decimal import Decimal
from typing import Dict, Any
from .evaluator import ExpressionEvaluator


def validate_numeric_expression(expr: str, context: Dict[str, Any]) -> None:
    """
    Used for:
    - part_length_equation
    - part_width_equation
    - quantity_equation
    - product dimension equations
    """
    evaluator = ExpressionEvaluator(context)
    result = evaluator.eval(expr)

    if not isinstance(result, (int, float, Decimal)):
        raise ValueError("Expression must return a number")


def validate_boolean_expression(expr: str, context: Dict[str, Any]) -> None:
    """
    Used for:
    - validation_expression
    """
    evaluator = ExpressionEvaluator(context)
    result = evaluator.eval(expr)

    if not isinstance(result, bool):
        raise ValueError("Expression must return boolean (True / False)")
