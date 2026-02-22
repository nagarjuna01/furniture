from decimal import Decimal
from .material_cost import calculate_material_cost
from .hardware_cost import calculate_hardware_cost
from .waste_calculator import calculate_waste


def build_bom(evaluated_parts: list[dict], hardware_rules: list[dict]) -> dict:
    """
    Builds a traceable BOM from evaluated parts.
    DOES NOT apply pricing strategy.
    """

    bom = {
        "materials": [],
        "hardware": [],
        "totals": {
            "material_cp": Decimal("0"),
            "hardware_cp": Decimal("0"),
            "waste_cp": Decimal("0"),
        }
    }

    # ----------------------------
    # Materials
    # ----------------------------
    for part in evaluated_parts:
        qty = Decimal(str(part.get("quantity", 1)))

        material_cost = calculate_material_cost(part) * qty
        waste_info = calculate_waste(part)

        bom["materials"].append({
            "part": part["name"],
            "material": part["material"],
            "quantity": qty,
            "material_cost": material_cost,
            "waste": {
                "amount": waste_info.get("cost", Decimal("0")),
                "reason": waste_info.get("reason"),
                "type": waste_info.get("type"),  # sheet / trim / kerf
            }
        })

        bom["totals"]["material_cp"] += material_cost
        bom["totals"]["waste_cp"] += waste_info.get("cost", Decimal("0"))

    # ----------------------------
    # Hardware
    # ----------------------------
    hardware_cp = calculate_hardware_cost(hardware_rules)

    bom["hardware"] = hardware_rules
    bom["totals"]["hardware_cp"] = hardware_cp

    return bom
