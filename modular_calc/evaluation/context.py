# evaluation/context.py
from decimal import Decimal
from typing import Dict, Optional,Any

def to_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))

class ProductContext:
    """Build context for product/part evaluation."""

    def __init__(self, product_dims: Dict[str, Any], parameters: Optional[Dict[str, Any]] = None, part_thickness: Optional[float] = None):
        self.ctx = {
            "product_length": to_decimal(product_dims.get("product_length", 0)),
            "product_width": to_decimal(product_dims.get("product_width", 0)),
            "product_height": to_decimal(product_dims.get("product_height", 0)),
            "quantity": to_decimal(product_dims.get("quantity", 1)),
        }
        if part_thickness is not None:
            self.ctx["part_thickness"] = to_decimal(part_thickness)
        if parameters:
            for k, v in parameters.items():
                self.ctx[k] = to_decimal(v)

    def get_context(self) -> Dict[str, Decimal]:
        return self.ctx
