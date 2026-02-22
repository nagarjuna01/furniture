import unittest
from decimal import Decimal

from modular_calc.evaluation.cutlist_optimizer import (
    CutlistOptimizer,
    PartRect,
)


class TestCutlistAreaConservation(unittest.TestCase):

    def test_area_conservation(self):
        parts = [
            PartRect(
                name="Panel A",
                width=Decimal("600"),
                height=Decimal("500"),
                quantity=2,
                grain="none",
            ),
            PartRect(
                name="Panel B",
                width=Decimal("400"),
                height=Decimal("300"),
                quantity=1,
                grain="none",
            ),
        ]

        optimizer = CutlistOptimizer(sheet_width_mm=2440, sheet_height_mm=1220)
        result = optimizer.optimize(parts)

        used_area = sum(
            sheet["used_area"] for sheet in result["sheets"]
        )

        expected_area = (
            Decimal("600") * Decimal("500") * 2 +
            Decimal("400") * Decimal("300")
        )

        self.assertEqual(used_area, expected_area)


if __name__ == "__main__":
    unittest.main()
