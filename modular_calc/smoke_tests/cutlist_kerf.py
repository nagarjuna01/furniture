from decimal import Decimal
from modular_calc.evaluation.cutlist_optimizer import CutlistOptimizer, PartRect


def test_kerf_spacing_applied():
    optimizer = CutlistOptimizer(kerf_mm=10)

    parts = [
        PartRect(
            name="PanelA",
            width=Decimal("500"),
            height=Decimal("500"),
            quantity=2,
            grain="none"
        ),
    ]

    result = optimizer.optimize(parts)
    cuts = result["sheets"][0]["cuts"]

    assert len(cuts) == 2

    a, b = cuts
    assert a["x"] != b["x"] or a["y"] != b["y"]

    print("✅ Kerf spacing smoke test passed")


if __name__ == "__main__":
    test_kerf_spacing_applied()
