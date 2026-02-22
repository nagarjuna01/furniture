# modular_calc/utils/safe_eval.py

import math
import operator

ALLOWED_NAMES = {
    # math
    **{k: getattr(math, k) for k in dir(math) if not k.startswith("_")},
    # builtins
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
}

ALLOWED_OPERATORS = {
    "+", "-", "*", "/", "//", "%", "**",
    "<", "<=", ">", ">=", "==", "!=",
    "and", "or", "not",
}

def safe_eval(expr: str, context: dict):
    """
    Safely evaluate a mathematical / boolean expression
    using a restricted namespace.
    """

    if not isinstance(expr, str):
        raise ValueError("Expression must be a string")

    # Compile first (catches syntax errors early)
    code = compile(expr, "<expression>", "eval")

    # Block any forbidden names
    for name in code.co_names:
        if name not in context and name not in ALLOWED_NAMES:
            raise ValueError(f"Unknown variable or function: {name}")

    return eval(
        code,
        {"__builtins__": {}},
        {**ALLOWED_NAMES, **context},
    )
