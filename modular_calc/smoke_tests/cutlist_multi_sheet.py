from decimal import Decimal
from modular_calc.evaluation.cutlist_optimizer import CutlistOptimizer, PartRect


def test_multiple_sheets_created():
    optimizer = CutlistOptimizer(
        sheet_width_mm=1000,
        sheet_height_mm=1000
    )

    parts = [
        PartRect(
            name="BigPanel",
            width=Decimal("900"),
            height=Decimal("900"),
            quantity=3,
            grain="none"
        )
    ]

    result = optimizer.optimize(parts)

    assert result["total_sheets"] == 3

    for sheet in result["sheets"]:
        assert len(sheet["cuts"]) == 1

    print("✅ Multi-sheet smoke test passed")


if __name__ == "__main__":
    test_multiple_sheets_created()

def test_waste_sanity():
    optimizer = CutlistOptimizer()

    parts = [
        PartRect(
            name="Panel",
            width=Decimal("1000"),
            height=Decimal("1000"),
            quantity=1,
            grain="none"
        )
    ]

    result = optimizer.optimize(parts)
    sheet = result["sheets"][0]

    total = sheet["width"] * sheet["height"]
    used = sheet["used_area"]
    remaining = sheet["remaining_area"]

    assert used + remaining <= total
    assert 0 <= sheet["waste_percent"] <= 100

    print("✅ Waste sanity smoke test passed")