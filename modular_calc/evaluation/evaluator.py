#modular_calc/evaluation/evaluator.py
from asteval import Interpreter
from decimal import Decimal
from typing import Dict, Any

_ALLOWED_NAMES = {
    "min": min,
    "max": max,
    "round": round,
    "abs": abs
}

class ExpressionEvaluator:
    def __init__(self, context: Dict[str, Any]):
        # Convert Decimals to Floats for asteval compatibility
        # and ensure all keys are strictly lowercase
        self.context = {}
        for k, v in context.items():
            val = float(v) if isinstance(v, (Decimal, float, int)) else v
            self.context[k.lower()] = val

    def eval(self, expr: str) -> Any:
        if not expr:
            return None
            
        # 1. Standardize expression
        clean_expr = expr.lower().strip()
        
        # 2. Initialize Interpreter with our context as the initial symtable
        # This is more reliable than updating symtable later
        aeval = Interpreter(usersyms={**_ALLOWED_NAMES, **self.context}, minimal=True)
        result = aeval(clean_expr)
        
        if len(aeval.error) > 0:
            # Grab the specific error details
            err = aeval.error[0]
            raise ValueError(f"Eval error for '{clean_expr}': {err.msg}")
            
        return result