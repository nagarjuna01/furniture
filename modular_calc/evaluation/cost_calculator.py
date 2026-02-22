#modular_calc/evaluation/cost_calculator.py
from decimal import Decimal
from typing import Dict, List

class CostCalculator:
    """
    Aggregates costs already computed by BOMBuilder.
    NEVER recomputes geometry or unit costs.
    """

    def __init__(self, bom: Dict):
        self.bom = bom
        self.part_costs = []
        self.hardware_costs = []
        self.total_cost = Decimal("0")

    def calculate(self):
        self._collect_parts()
        self._collect_hardware()
        self.total_cost = (
            sum(p["total_cost"] for p in self.part_costs) +
            sum(h["total_cost"] for h in self.hardware_costs)
        )
        
    def _collect_parts(self):
        
        for part in self.bom.get("parts", []):
            try:
                # Use .get() with defaults to prevent crashes, but log the failure
                cp = Decimal(str(part.get("cp", 0)))
                sp = Decimal(str(part.get("sp", 0)))
                
                # NO SILENT KILLERS: Capture nested values or default to 0
                m_cp = Decimal(str(part.get("material_cost", {}).get("cp", 0) if isinstance(part.get("material_cost"), dict) else part.get("material_cost", 0)))
                e_cp = Decimal(str(part.get("edgeband_cost", {}).get("cp", 0) if isinstance(part.get("edgeband_cost"), dict) else 0))
                
                self.part_costs.append({
                    "name": part.get("name", "Unknown Part"),
                    "material_cost": m_cp,
                    "edgeband_cost": e_cp,
                    "total_cost": cp,
                    "sell_price": sp,
                })
            except Exception as e:
                print(f"!!! [ACCOUNTANT_FATAL] Error processing part {part.get('name')}: {str(e)}")
                raise e

    def _collect_hardware(self):
        
        for hw in self.bom.get("hardware", []):
            try:
                # IMPORTANT: Use total_cp (Qty * Unit CP) for the calculator's sum
                # HardwareEvaluator returns 'total_cp' and 'total_sp'
                line_cp = Decimal(str(hw.get("total_cp", hw.get("cp", 0))))
                line_sp = Decimal(str(hw.get("total_sp", hw.get("sp", 0))))
                
                self.hardware_costs.append({
                    "name": hw.get("name"),
                    "quantity": hw.get("quantity"),
                    "total_cost": line_cp, 
                    "sell_price": line_sp,
                })
            except Exception as e:
                print(f"!!! [ACCOUNTANT_FATAL] Error processing hardware {hw.get('name')}: {str(e)}")
                raise e
