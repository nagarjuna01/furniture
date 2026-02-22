from decimal import Decimal
from modular_calc.evaluation.cutlist_optimizer import CutlistOptimizer, PartRect


def test_grain_orientation_respected():
    optimizer = CutlistOptimizer(
        sheet_width_mm=2440,
        sheet_height_mm=2440  # allow vertical fit
    )

    parts = [
        PartRect(
            name="VerticalGrainPanel",
            width=Decimal("600"),
            height=Decimal("2000"),
            quantity=1,
            grain="vertical"
        ),
        PartRect(
            name="FreeRotatePanel",
            width=Decimal("2000"),
            height=Decimal("600"),
            quantity=1,
            grain="none"
        ),
    ]

    result = optimizer.optimize(parts)
    cuts = result["sheets"][0]["cuts"]

    # DEBUG visibility (smoke test style)
    print("Cuts:", cuts)

    vertical = next(c for c in cuts if c["name"] == "VerticalGrainPanel")

    # Grain locked → must not rotate
    assert vertical["width"] == Decimal("600")
    assert vertical["height"] == Decimal("2000")

    print("✅ Grain orientation smoke test passed")


if __name__ == "__main__":
    test_grain_orientation_respected()
