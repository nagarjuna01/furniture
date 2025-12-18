from typing import Dict
from .evaluator import ExpressionEvaluator
from .context import ProductContext, to_decimal
from decimal import Decimal

class PartEvaluator:
    """Evaluate part dimensions, quantity, material, edgebands, and assets."""

    def __init__(self, part_template, product_dims: Dict[str, Decimal], parameters: Dict[str, Decimal]):
        self.part_template = part_template
        # Build evaluation context
        self.context = ProductContext(
            product_dims,
            parameters,
            part_thickness=part_template.part_thickness_mm
        ).get_context()
        self.evaluator = ExpressionEvaluator(self.context)

    def evaluate(self) -> Dict[str, any]:
        """Return part evaluation dict with dimensions, quantity, material, edgebands, assets."""

        # Evaluate geometric expressions
        length = self.evaluator.eval(self.part_template.part_length_equation)
        width = self.evaluator.eval(self.part_template.part_width_equation)
        qty = self.evaluator.eval(self.part_template.part_qty_equation)

        # Shape wastage multiplier
        shape_wastage = to_decimal(self.part_template.shape_wastage_multiplier)

        # Material selection
        material_obj = self._select_material_obj()

        # Edgeband selection per side
        edgeband_objs = self._select_edgeband_objs()

        # 3D/2D asset references
        three_d_asset = self.part_template.three_d_asset.url if self.part_template.three_d_asset else None
        two_d_template_svg = self.part_template.two_d_template_svg or getattr(self.part_template.product, "two_d_template_svg", None)

        return {
            "name": self.part_template.name,
            "length": to_decimal(length),
            "width": to_decimal(width),
            "quantity": to_decimal(qty),
            "thickness": to_decimal(self.part_template.part_thickness_mm),
            "shape_wastage_multiplier": shape_wastage,
            "grain_direction": self.part_template.grain_direction,
            "material_obj": material_obj,           # Material object with cp/sp
            "edgeband_objs": edgeband_objs,         # Dict[side] -> edgeband object
            "three_d_asset": three_d_asset,
            "two_d_template_svg": two_d_template_svg,
        }

    def _select_material_obj(self):
        """Return the default material object from whitelist."""
        default_material = self.part_template.material_whitelist.filter(is_default=True).first()
        if default_material:
            return default_material.material
        # fallback: pick first from whitelist
        fallback = self.part_template.material_whitelist.first()
        return fallback.material if fallback else None

    def _select_edgeband_objs(self):
        """Return dict: side -> edge band object."""
        sides = ["top", "bottom", "left", "right"]
        result = {}

        for side in sides:
            default = self.part_template.edgeband_whitelist.filter(side=side, is_default=True).first()
            if default:
                result[side] = default.edgeband
                continue

            fallback = self.part_template.edgeband_whitelist.filter(side=side).first()
            result[side] = fallback.edgeband if fallback else None

        return result
