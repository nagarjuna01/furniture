# modular_calc/evaluation/quotation_generator.py
from decimal import Decimal
from typing import Dict, List

from .cost_calculator import CostCalculator
from .cutlist_optimizer import CutlistOptimizer, PartRect
from .pricing_resolver import PricingResolver


class QuotationGenerator:
    """
    Generates customer-ready quotation.
    Orchestrates pricing, not calculations.
    """

    def __init__(
        self,
        bom: Dict,
        sheet_width_mm: int = 2440,
        sheet_height_mm: int = 1220,
        kerf_mm: int = 3,
    ):
        self.bom = bom
        self.cost_calculator = CostCalculator(bom)
        self.optimizer = CutlistOptimizer(
            sheet_width_mm=sheet_width_mm,
            sheet_height_mm=sheet_height_mm,
            kerf_mm=kerf_mm,
        )

    def _build_part_rects(self) -> List[PartRect]:
        rects = []
        for part in self.bom["parts"]:
            rects.append(
                PartRect(
                    width=part["width_mm"],
                    height=part["height_mm"],
                    quantity=part["quantity"],
                    name=part["name"],
                    grain=part.get("grain", "none"),
                )
            )
        return rects

    def generate(self) -> Dict:
        # 1️⃣ Technical optimization
        cutlist = self.optimizer.optimize(self._build_part_rects())

        # 2️⃣ Cost aggregation (sheet-based CP already applied upstream)
        pricing = PricingResolver(
            bom=self.bom,
            cost_calculator=self.cost_calculator,
            cutlist=cutlist,
        ).resolve()

        # 3️⃣ Final quotation assembly
        return {
            "product_name": self.bom.get("product_name"),
            "pricing": pricing,
            "cutlist_summary": {
                "total_sheets": cutlist["total_sheets"],
                "waste_percent": cutlist["total_waste_percent"],
            },
            "parts": pricing["pricing_options"]["area"]["parts"],
            "hardware": pricing["pricing_options"]["area"]["hardware"],
        }
