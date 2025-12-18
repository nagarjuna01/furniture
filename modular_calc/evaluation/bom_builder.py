# evaluation/bom_builder.py
from typing import Dict, List
from decimal import Decimal
from .part_evaluator import PartEvaluator
from .hardware_evaluator import HardwareEvaluator
from .context import to_decimal

class BOMBuilder:
    """Generate full BOM for a product including parts, materials, edge bands, hardware, 3D/2D assets, CP/SP, and max discount."""

    def __init__(self, product, product_dims: Dict[str, Decimal], parameters: Dict[str, Decimal]):
        self.product = product
        self.product_dims = product_dims
        self.parameters = parameters

    def build_parts(self) -> List[Dict]:
        parts = []
        for part_template in self.product.part_templates.all():
            evaluator = PartEvaluator(part_template, self.product_dims, self.parameters)
            part_data = evaluator.evaluate()

            # Apply shape wastage to quantity
            qty_with_wastage = (part_data["quantity"] * part_data["shape_wastage_multiplier"]).quantize(Decimal("1.00"))
            part_data["quantity_with_wastage"] = qty_with_wastage

            # Include 3D/2D assets
            part_data["three_d_asset"] = part_template.three_d_asset.url if part_template.three_d_asset else self.product.three_d_asset.url if self.product.three_d_asset else None
            part_data["two_d_template_svg"] = part_template.two_d_template_svg or self.product.two_d_template_svg or None

            # Compute material cost
            material_cost = self._compute_material_cost(part_template, part_data)
            # Compute edgeband cost
            edgeband_cost = self._compute_edgeband_cost(part_template, part_data)
            # Compute hardware cost for this part
            hardware_cost = self._compute_hardware_cost(part_template)

            # Compute CP, SP, max discount
            pricing = self._compute_prices(part_data, material_cost, edgeband_cost, hardware_cost)

            part_data.update({
                "material_cost": material_cost,
                "edgeband_cost": edgeband_cost,
                "hardware_cost": hardware_cost,
                **pricing,
            })

            parts.append(part_data)
        return parts

    def build_hardware(self) -> List[Dict]:
        hardware_items = []
        # Product-level hardware
        for rule in self.product.hardware_rules.all():
            evaluator = HardwareEvaluator(rule, {**self.product_dims, **self.parameters})
            hardware_items.append(evaluator.evaluate())
        # Part-level hardware
        for part_template in self.product.part_templates.all():
            for rule in part_template.hardware_rules.all():
                evaluator = HardwareEvaluator(rule, {**self.product_dims, **self.parameters})
                hardware_items.append(evaluator.evaluate())
        return hardware_items

    def build_bom(self) -> Dict:
        parts = self.build_parts()
        hardware_items = self.build_hardware()

        # Aggregate total CP and SP
        total_cp = sum([p["cp"] for p in parts])
        total_sp = sum([p["sp"] for p in parts])
        max_discount = sum([p["max_discount"] for p in parts])

        return {
            "product_name": self.product.name,
            "parts": parts,
            "hardware": hardware_items,
            "total_cp": total_cp.quantize(Decimal("1.00")),
            "total_sp": total_sp.quantize(Decimal("1.00")),
            "max_discount": max_discount.quantize(Decimal("1.00")),
        }

    def _compute_material_cost(self, part_template, part_data: Dict) -> Decimal:
        """Compute material cost in mm using CP from material model."""
        material_obj = part_template.material_whitelist.filter(is_default=True).first()
        if not material_obj:
            return Decimal("0")
        # area in mm²
        area_mm2 = part_data["length"] * part_data["width"]
        # multiply by thickness for volume if needed
        cost = area_mm2 * part_data["thickness"] * material_obj.material.cp * part_data["quantity_with_wastage"]
        return cost.quantize(Decimal("1.00"))

    def _compute_edgeband_cost(self, part_template, part_data: Dict) -> Decimal:
        """Compute edgeband cost for all sides in mm."""
        total = Decimal("0")
        sides = ["top", "bottom", "left", "right"]
        for side in sides:
            eb_obj = part_template.edgeband_whitelist.filter(edgeband__is_default=True, edgeband__side=side).first()
            if eb_obj and eb_obj.edgeband and hasattr(eb_obj.edgeband, "cp"):
                length_mm = part_data["length"] if side in ["top", "bottom"] else part_data["width"]
                total += length_mm * eb_obj.edgeband.cp * part_data["quantity_with_wastage"]
        return total.quantize(Decimal("1.00"))

    def _compute_hardware_cost(self, part_template) -> Decimal:
        """Compute cost of all hardware attached to this part."""
        total = Decimal("0")
        for rule in part_template.hardware_rules.all():
            if hasattr(rule.hardware, "cp"):
                total += rule.quantity * rule.hardware.cp
        return total.quantize(Decimal("1.00"))

    def _compute_prices(self, part_data: Dict, material_cost: Decimal, edgeband_cost: Decimal, hardware_cost: Decimal) -> Dict[str, Decimal]:
        """Compute CP, SP, and max discount for a part."""
        cp = material_cost + edgeband_cost + hardware_cost
        # Use SP from material if available, otherwise default markup
        sp = part_data.get("material") and part_data["material"].sp or cp * Decimal("1.5")
        max_discount = sp - (cp * Decimal("1.2"))  # SP - (CP + 20% CP)
        return {
            "cp": cp.quantize(Decimal("1.00")),
            "sp": sp.quantize(Decimal("1.00")),
            "max_discount": max_discount.quantize(Decimal("1.00")),
        }
