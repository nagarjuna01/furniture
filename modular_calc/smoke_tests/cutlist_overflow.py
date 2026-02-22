from decimal import Decimal
from modular_calc.evaluation.cutlist_optimizer import CutlistOptimizer, PartRect


def test_part_larger_than_sheet():
    optimizer = CutlistOptimizer(
        sheet_width_mm=2440,
        sheet_height_mm=1220
    )

    parts = [
        PartRect(
            name="OversizedPanel",
            width=Decimal("3000"),
            height=Decimal("1500"),
            quantity=1,
            grain="none"
        )
    ]

    result = optimizer.optimize(parts)

    # Optimizer does not crash
    assert result["total_sheets"] >= 1

    # No part should be placed
    total_cuts = sum(len(s["cuts"]) for s in result["sheets"])
    assert total_cuts == 0

    print("✅ Oversized part smoke test passed")


if __name__ == "__main__":
    test_part_larger_than_sheet()
