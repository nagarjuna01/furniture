from decimal import Decimal

def calculate_hardware_costs(hardware_rules):
    """
    Returns detailed CP/SP breakdown for hardware.
    """

    total_cp = Decimal("0.00")
    total_sp = Decimal("0.00")
    breakdown = []

    for rule in hardware_rules:
        if not getattr(rule, "applies", False):
            continue

        qty = Decimal(str(rule.quantity))
        cp = Decimal(str(rule.hardware.cp)) * qty
        sp = Decimal(str(rule.hardware.sp)) * qty

        breakdown.append({
            "name": rule.hardware.name,
            "quantity": qty,
            "unit_cp": rule.hardware.cp,
            "unit_sp": rule.hardware.sp,
            "total_cp": cp,
            "total_sp": sp,
        })

        total_cp += cp
        total_sp += sp

    return {
        "items": breakdown,
        "total_cp": total_cp.quantize(Decimal("0.01")),
        "total_sp": total_sp.quantize(Decimal("0.01")),
    }
