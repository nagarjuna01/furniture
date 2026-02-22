import unittest
from decimal import Decimal

from modular_calc.evaluation.cost_calculator import CostCalculator


class TestSheetCosting(unittest.TestCase):

    def test_sheet_cost_increases_with_usage(self):
        material = {
            "name": "PLY_18MM",
            "sheet_width": Decimal("2440"),
            "sheet_height": Decimal("1220"),
            "sheet_cost": Decimal("2500"),
        }

        calc = CostCalculator(material)

        low_usage = {
            "total_sheets": 1,
            "used_area": Decimal("500000"),
        }

        high_usage = {
            "total_sheets": 1,
            "used_area": Decimal("1500000"),
        }

        cost_low = calc.calculate(low_usage)
        cost_high = calc.calculate(high_usage)

        self.assertGreater(cost_high, cost_low)


if __name__ == "__main__":
    unittest.main()
