from decimal import Decimal

def calculate_waste(part: dict) -> dict:
    """
    ESTIMATED waste.
    Used only before cutlist optimization.
    """
    part_area = Decimal(str(part["length"])) * Decimal(str(part["width"]))
    qty = Decimal(str(part.get("quantity", 1)))

    used_area = part_area * qty

    return {
        "type": "estimated",
        "area": Decimal("0.00"),   # no fake math
        "cost": Decimal("0.00"),
        "reason": "Cutlist not applied yet"
    }

from decimal import Decimal

def calculate_waste_from_cutlist(cutlist: dict, sheet_area: Decimal) -> dict:
    """
    Accurate waste derived from optimizer output.
    """
    total_sheets = Decimal(str(cutlist["total_sheets"]))
    waste_percent = Decimal(str(cutlist["total_waste_percent"]))

    total_area = sheet_area * total_sheets
    waste_area = (total_area * waste_percent / Decimal("100")).quantize(Decimal("0.01"))

    return {
        "type": "sheet",
        "area": waste_area,
        "percent": waste_percent,
        "reason": "Cutlist optimizer"
    }
