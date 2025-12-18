from decimal import Decimal
from typing import Dict
from .cost_calculator import CostCalculator
from .cutlist_optimizer import CutlistOptimizer

class QuotationGenerator:
    """Generate customer-ready quotation including BOM, costs, and suggested batch."""

    def __init__(self, bom: Dict, stock_sheet_size: int = 2440):
        self.bom = bom
        self.stock_sheet_size = stock_sheet_size
        self.cost_calculator = CostCalculator(bom)
        self.optimizer = CutlistOptimizer(bom, stock_sheet_size)
        self.recommended_quantity: int = 1
        self.total_cost: Decimal = Decimal("0")
        self.quotation: Dict = {}

    def generate(self, max_batch_quantity: int = 50) -> Dict:
        self.cost_calculator.calculate()
        self.total_cost = self.cost_calculator.total_cost
        self.recommended_quantity = self.optimizer.optimize(max_batch_quantity)
        self.quotation = {
            "product_name": self.bom.get("product_name"),
            "parts": self.cost_calculator.part_costs,
            "hardware": self.cost_calculator.hardware_costs,
            "recommended_batch_quantity": self.recommended_quantity,
            "total_cost": self.total_cost
        }
        return self.quotation
