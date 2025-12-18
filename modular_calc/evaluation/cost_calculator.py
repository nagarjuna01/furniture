from decimal import Decimal
from typing import Dict, List

class CostCalculator:
    """Calculate material and hardware costs based on BOM and shape wastage."""

    def __init__(self, bom: Dict):
        self.bom = bom
        self.part_costs: List[Dict] = []
        self.hardware_costs: List[Dict] = []
        self.total_cost: Decimal = Decimal("0")

    def calculate(self):
        self._calculate_parts()
        self._calculate_hardware()
        self.total_cost = sum(p["total_cost"] for p in self.part_costs) + sum(h["total_cost"] for h in self.hardware_costs)

    def _calculate_parts(self):
        for part in self.bom["parts"]:
            qty_with_wastage = Decimal(part["quantity"]) * Decimal(part.get("shape_wastage_multiplier", 1))
            unit_cost = self._get_material_cost(part)  # Implement this to fetch from DB or pricing table
            total_cost = qty_with_wastage * unit_cost
            self.part_costs.append({
                "name": part["name"],
                "length": part["length"],
                "width": part["width"],
                "thickness": part["thickness"],
                "quantity": part["quantity"],
                "qty_with_wastage": qty_with_wastage,
                "unit_cost": unit_cost,
                "total_cost": total_cost
            })

    def _calculate_hardware(self):
        for hw in self.bom["hardware"]:
            unit_cost = self._get_hardware_cost(hw["hardware"])  # Implement this
            total_cost = Decimal(hw["quantity"]) * unit_cost
            self.hardware_costs.append({
                "hardware": hw["hardware"],
                "quantity": hw["quantity"],
                "unit_cost": unit_cost,
                "total_cost": total_cost
            })

    def _get_material_cost(self, part: Dict) -> Decimal:
        # Placeholder: Replace with DB lookup or pricing logic
        return Decimal("5.0")  # Example unit cost per part

    def _get_hardware_cost(self, hardware_name: str) -> Decimal:
        # Placeholder: Replace with DB lookup or pricing logic
        return Decimal("2.0")  # Example hardware cost per unit
