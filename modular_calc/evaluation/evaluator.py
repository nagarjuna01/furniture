# evaluation/evaluator.py
from asteval import Interpreter
from decimal import Decimal
from typing import Dict, Any, Optional

_ALLOWED_NAMES = {
    "min": min,
    "max": max,
    "round": round,
    "abs": abs
}

class ExpressionEvaluator:
    """Safely evaluate math expressions in a restricted context."""

    def __init__(self, context: Dict[str, Any]):
        self.context = context

    def eval(self, expr: str) -> Any:
        aeval = Interpreter(minimal=True)
        aeval.symtable.update(_ALLOWED_NAMES)
        aeval.symtable.update(self.context)
        result = aeval(expr)
        if aeval.error:
            raise ValueError(f"Eval error for '{expr}': {aeval.error[0].get_error()}")
        return result
