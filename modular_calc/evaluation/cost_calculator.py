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
            # 1. IDENTIFY THICKNESS (The Source of Truth)
            # We check part-specific thickness first, then fallback to Global Variable @ST
            part_thickness = Decimal(str(part.get("material_thickness", self.global_vars.get('@ST', 18))))

            # 2. RESOLVE GEOMETRY
            # We convert the equations into actual numbers (mm)
            length = self._resolve_equation(part["length_eq"], part_thickness)
            width = self._resolve_equation(part["width_eq"], part_thickness)

            # 3. CALCULATE QUANTITY & AREA
            qty = Decimal(str(part["quantity"]))
            wastage = Decimal(str(part.get("shape_wastage_multiplier", 1)))
            qty_with_wastage = qty * wastage
            
            # Area in Square Meters (mm * mm / 1,000,000)
            area_m2 = (length * width) / Decimal("1000000")

            # 4. FETCH COST & CALCULATE TOTAL
            # This calls your material DB to get price per sqm based on the part/thickness
            unit_rate = self._get_material_cost(part) 
            
            total_cost = area_m2 * qty_with_wastage * unit_rate

            # 5. STORE RESULTS for the Quote/BOM
            self.part_costs.append({
                "name": part["name"],
                "calculated_length": length.quantize(Decimal("0.1")), # Round to 1 decimal place (0.1mm)
                "calculated_width": width.quantize(Decimal("0.1")),
                "thickness": part_thickness,
                "quantity": qty,
                "area_m2": area_m2.quantize(Decimal("0.0001")), # 4 decimals for area accuracy
                "total_cost": total_cost.quantize(Decimal("0.01")) # 2 decimals for currency
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
