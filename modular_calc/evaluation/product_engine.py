# evaluation/product_engine.py

from decimal import Decimal
from typing import Dict
from .bom_builder import BOMBuilder
from .cutlist_optimizer import CutlistOptimizer, PartRect
from .evaluator import ExpressionEvaluator


class ProductEngine:
    """
    Master coordinator:
    - Supports multi-product/modular assemblies
    - Validates product rules
    - Builds BOM
    - Computes CP/SP totals including labour, assembly, tax, shipping
    - Advises discount and minimum selling price
    - Runs grain-aware sheet optimizer
    - Supports multi-quantity what-if pricing
    """

    TAX_MAP = {
        "wood": Decimal("0.18"),
        "metal": Decimal("0.12"),
        "glass": Decimal("0.28"),
        "fiber": Decimal("0.18"),
        "default": Decimal("0.18"),
    }

    #SHIPPING_RATE_PER_KG = Decimal("5.00")  # example CP
    #SHIPPING_SP_RATE_PER_KG = Decimal("7.00")  # example SP

    def __init__(self, product, product_dims: dict, parameters: dict, quantities: list[int] = None):
        self.product = product
        self.product_dims = {k: Decimal(str(v)) for k, v in product_dims.items()}
        self.parameters = {k: Decimal(str(v)) for k, v in parameters.items()}
        self.quantities = quantities or [self.product_dims.get("quantity", 1)]

    # ----------------------------
    # Product validation
    # ----------------------------
    def validate_product(self) -> bool:
        expr = getattr(self.product, "product_validation_expression", None)
        if not expr:
            return True
        evaluator = ExpressionEvaluator({**self.product_dims, **self.parameters})
        return bool(evaluator.eval(expr))

    # ----------------------------
    # Main execution
    # ----------------------------
    def run(self) -> dict:

        if not self.validate_product():
            raise ValueError(f"Product '{self.product.name}' failed validation rules.")

        all_quotes = {}

        # For each what-if quantity
        for qty in self.quantities:

            dims = self.product_dims.copy()
            dims["quantity"] = Decimal(str(qty))

            # Build full BOM (multi-product assembly)
            bom = self._build_full_bom(self.product, dims)

            # ----------------------------
            # CUTLIST OPTIMIZATION
            # ----------------------------
            cutlist_input = [
                PartRect(
                    width=p["width"],
                    height=p["length"],
                    quantity=int(p["quantity_with_wastage"]),
                    name=p["name"],
                    grain=p.get("grain_direction", "none")
                )
                for p in bom["parts"]
            ]

            optimizer = CutlistOptimizer(sheet_width_mm=2440, sheet_height_mm=1220)
            cutplan = optimizer.optimize(cutlist_input)
            bom["cutlist"] = cutplan

            # ----------------------------
            # PRICE + MARGINS + DISCOUNT
            # ----------------------------
            summary = self._calculate_totals(bom)

            all_quotes[str(qty)] = {
                "bom": bom,
                "summary": summary,
            }

        return {
            "product": self.product.name,
            "quotes": all_quotes,
        }

    # ----------------------------
    # Build BOM recursively for sub-products/modules
    # ----------------------------
    def _build_full_bom(self, product, dims: Dict) -> dict:
        bom_builder = BOMBuilder(product, dims, self.parameters)
        bom = bom_builder.build_bom()

        # If product has sub-products/modules, include their BOMs
        if hasattr(product, "sub_products"):
            for sub in product.sub_products.all():
                sub_bom = self._build_full_bom(sub, dims)
                bom["parts"].extend(sub_bom["parts"])
                bom["hardware"].extend(sub_bom["hardware"])

        return bom

    # ----------------------------
    # Internal: total CP/SP + labour + tax + shipping + discount advisory
    # ----------------------------
    def _calculate_totals(self, bom: dict) -> dict:

        parts = bom["parts"]
        hardware = bom["hardware"]

        total_part_cp = Decimal("0")
        total_part_sp = Decimal("0")
        total_hw_cp = Decimal("0")
        total_hw_sp = Decimal("0")
        total_labour_cp = Decimal("0")
        total_labour_sp = Decimal("0")
        total_tax_cp = Decimal("0")
        total_tax_sp = Decimal("0")
        total_shipping_cp = Decimal("0")
        total_shipping_sp = Decimal("0")

        # PART TOTALS
        for p in parts:
            cp = p.get("total_cp", Decimal("0"))
            sp = p.get("total_sp", Decimal("0"))
            total_part_cp += cp
            total_part_sp += sp

            # Labour & assembly
            total_labour_cp += p.get("labour_cp", Decimal("0"))
            total_labour_sp += p.get("labour_sp", Decimal("0"))

            # Tax
            mat_type = p.get("material_type", "default")
            tax_rate = self.TAX_MAP.get(mat_type, self.TAX_MAP["default"])
            total_tax_cp += (cp * tax_rate).quantize(Decimal("1.00"))
            total_tax_sp += (sp * tax_rate).quantize(Decimal("1.00"))

            # Shipping (based on weight)
            #weight = p.get("weight_kg", Decimal("0"))
            #total_shipping_cp += weight * self.SHIPPING_RATE_PER_KG
            #total_shipping_sp += weight * self.SHIPPING_SP_RATE_PER_KG

        # HARDWARE TOTALS
        for h in hardware:
            qty = Decimal(h["quantity"])
            hw_obj = h.get("hardware_obj")
            if hw_obj and hasattr(hw_obj, "cp"):
                total_hw_cp += hw_obj.cp * qty
                total_hw_sp += hw_obj.sp * qty
            else:
                total_hw_cp += qty
                total_hw_sp += qty

        total_cp = total_part_cp + total_hw_cp + total_labour_cp + total_shipping_cp + total_tax_cp
        total_sp = total_part_sp + total_hw_sp + total_labour_sp + total_shipping_sp + total_tax_sp

        # 20% required margin (minimum selling price)
        min_sell = (total_cp * Decimal("1.20")).quantize(Decimal("1.00"))
        max_discount = (total_sp - min_sell).quantize(Decimal("1.00"))
        margin = (total_sp - total_cp).quantize(Decimal("1.00"))

        return {
            "total_part_cp": total_part_cp.quantize(Decimal("1.00")),
            "total_part_sp": total_part_sp.quantize(Decimal("1.00")),
            "total_hardware_cp": total_hw_cp.quantize(Decimal("1.00")),
            "total_hardware_sp": total_hw_sp.quantize(Decimal("1.00")),
            "total_labour_cp": total_labour_cp.quantize(Decimal("1.00")),
            "total_labour_sp": total_labour_sp.quantize(Decimal("1.00")),
            #"total_shipping_cp": total_shipping_cp.quantize(Decimal("1.00")),
            #"total_shipping_sp": total_shipping_sp.quantize(Decimal("1.00")),
            "total_tax_cp": total_tax_cp.quantize(Decimal("1.00")),
            "total_tax_sp": total_tax_sp.quantize(Decimal("1.00")),
            "total_cp": total_cp.quantize(Decimal("1.00")),
            "total_sp": total_sp.quantize(Decimal("1.00")),

            # Pricing advisory
            "required_minimum_sell_price": min_sell,
            "max_discount_possible": max_discount,
            "profit_margin": margin,
            "can_offer_discount": max_discount > 0,
            "discount_percentage": (
                (max_discount / total_sp * 100).quantize(Decimal("1.00"))
                if total_sp else Decimal("0")
            ),
        }
