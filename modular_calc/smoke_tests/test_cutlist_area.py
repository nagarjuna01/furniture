from decimal import Decimal
from modular_calc.evaluation.cutlist_optimizer import CutlistOptimizer, PartRect

def test_area_conservation():
    optimizer = CutlistOptimizer(
        sheet_width=Decimal("2400"),
        sheet_height=Decimal("1200"),
        kerf=Decimal("3")
    )

    parts = [
        PartRect("A", 600, 600),
        PartRect("B", 600, 600),
        PartRect("C", 600, 600),
        PartRect("D", 600, 600),
    ]

    result = optimizer.optimize(parts)
    used_area = sum(c["width"] * c["height"] for c in result["cuts"])

    assert used_area == Decimal("1440000")
