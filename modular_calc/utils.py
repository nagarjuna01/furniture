from asteval import Interpreter
from decimal import Decimal

_ALLOWED_NAMES = {
    "min": min,
    "max": max,
    "round": round,
    "abs": abs
}

def build_context(product_dims: dict, part_thickness: float | int | None = None, extras: dict | None = None):
    """
    product_dims expects keys: product_length, product_width, product_height, product_depth, quantity
    """
    ctx = {
        "product_length": float(product_dims.get("product_length", 0)),
        "product_width":  float(product_dims.get("product_width", 0)),
        "product_height": float(product_dims.get("product_height", 0)),
        "product_depth":  float(product_dims.get("product_depth", 0)),
        "quantity":       float(product_dims.get("quantity", 1)),
    }
    if part_thickness is not None:
        ctx["part_thickness"] = Decimal(str(part_thickness)) # Cast thickness to Decimal
    if extras:
        # Ensure any passed extras are also converted if they are numbers
        for key, value in extras.items():
            if isinstance(value, (float, int)):
                 ctx[key] = Decimal(str(value))
            else:
                 ctx[key] = value
        
    return ctx


def eval_expr(expr: str, context: dict):
    """
    Safely evaluate expression using asteval with a restricted symbol table.
    """
    aeval = Interpreter(minimal=True)
    aeval.symtable.update(_ALLOWED_NAMES)
    aeval.symtable.update(context)
    result = aeval(expr)
    if aeval.error:
        raise ValueError(f"Eval error for '{expr}': {aeval.error[0].get_error()}")
    return result


def validate_product(product_validation_expression: str | None, product_dims: dict) -> bool:
    if not product_validation_expression:
        return True
    ctx = build_context(product_dims)
    out = eval_expr(product_validation_expression, ctx)
    return bool(out)
