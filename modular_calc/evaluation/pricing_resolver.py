from decimal import Decimal
from typing import Dict, Any


class PricingResolver:
    """
    Chooses pricing strategy.
    - NEVER computes costs itself
    - NEVER modifies BOM
    - ONLY aggregates and presents pricing views
    """

    def __init__(self, bom: dict, cost_calculator, cutlist: dict, sheet_price: Decimal,quantity: int = 1):
        self.bom = bom
        self.cost_calculator = cost_calculator
        self.cutlist = cutlist
        self.sheet_price = Decimal(sheet_price or 0)
        self.quantity = int(quantity)
        self.pricing = {
            "material_cost": 0.0,
            "hardware_cost": 0.0,
            "sheet_cost": 0.0,
            "total_cost": 0.0
        }

        self._calculated = False

    # -------------------------
    # Internal helpers
    # -------------------------

    def _ensure_calculated(self):
        if not self._calculated:
            self.cost_calculator.calculate()
            self._calculated = True

    def _sum_part_sell_price(self) -> Decimal:
        parts = self.cost_calculator.part_costs or []
        if isinstance(parts, dict):
            parts = parts.values()
        unit_sp = sum(Decimal(str(p.get("sell_price", 0))) for p in parts)
        return unit_sp * Decimal(str(self.quantity))

    # -------------------------
    # Pricing Views
    # -------------------------

    def area_pricing(self) -> Dict[str, Any]:
        self._ensure_calculated()
        # Area CP is theoretical (Parts + Hardware * Qty)
        batch_cp = self.cost_calculator.total_cost * Decimal(str(self.quantity))
        batch_sp = self._sum_part_sell_price()

        return {
            "mode": "area",
            "cp": batch_cp.quantize(Decimal("1.00")),
            "sp": batch_sp.quantize(Decimal("1.00")),
            "parts": self.cost_calculator.part_costs,
            "hardware": self.cost_calculator.hardware_costs,
        } 

    def sheet_pricing(self) -> Dict[str, Any]:
        if not self.cutlist:
            raise ValueError("[RESOLVER_FATAL] Cutlist required for sheet pricing logic.")
        self._ensure_calculated()
        total_sheets = Decimal(str(self.cutlist.get("total_sheets", 0)))
        hw_cost = sum(Decimal(str(h.get("cp", 0))) for h in self.cost_calculator.hardware_costs or [])
        sheet_batch_cp = (total_sheets * self.sheet_price) + (hw_cost * Decimal(str(self.quantity)))
        batch_sp = self._sum_part_sell_price()
        

        return {
            "mode": "sheet",
            "cp": sheet_batch_cp.quantize(Decimal("1.00")),
            "sp": batch_sp.quantize(Decimal("1.00")),
            "total_sheets": int(total_sheets),
            "waste_percent": self.cutlist.get("total_waste_percent"),
        }

    # -------------------------
    # Resolver
    # -------------------------

    def resolve(self) -> Dict[str, Any]:
        options = {
            "area": self.area_pricing(),
            "sheet": self.sheet_pricing(),
        }
        
        # Logic: If Sheet CP > Area CP, it means wastage is high. 
        # We must recommend 'sheet' mode to ensure the owner doesn't lose money.
        return {
            "pricing_options": options,
            "recommended": "sheet", 
            "integrity_meta": {
                "batch_size": self.quantity,
                "is_owner_safe": options['sheet']['sp'] > options['sheet']['cp']
            }
        }
