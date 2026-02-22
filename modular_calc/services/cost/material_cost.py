from decimal import Decimal

def calculate_material_cost_area_based(part: dict) -> Decimal:
    """
    Area-based material cost.
    Used for SP (selling price), NOT procurement.
    """

    length = Decimal(str(part["length"]))
    width = Decimal(str(part["width"]))
    qty = Decimal(str(part["quantity"]))

    material = part["material_obj"]
    rate = Decimal(str(material.rate_per_sqmm))

    area = length * width
    cost = area * rate * qty

    return cost.quantize(Decimal("0.01"))

from decimal import Decimal

def calculate_material_cost_area_based(part: dict) -> Decimal:
    """
    Area-based material cost.
    Used for SP (selling price), NOT procurement.
    """

    length = Decimal(str(part["length"]))
    width = Decimal(str(part["width"]))
    qty = Decimal(str(part["quantity"]))

    material = part["material_obj"]
    rate = Decimal(str(material.rate_per_sqmm))

    area = length * width
    cost = area * rate * qty

    return cost.quantize(Decimal("0.01"))
