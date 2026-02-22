from decimal import Decimal

def suggest_cost_optimizations(bom: dict) -> list[dict]:
    suggestions = []

    summary = bom.get("summary", {})
    material_cost = Decimal(str(summary.get("material_cost", 0)))
    waste_cost = Decimal(str(summary.get("waste_cost", 0)))

    if material_cost == 0:
        return suggestions

    waste_ratio = (waste_cost / material_cost).quantize(Decimal("0.01"))

    if waste_ratio > Decimal("0.20"):
        suggestions.append({
            "type": "warning",
            "category": "material_waste",
            "message": "High material waste detected.",
            "details": {
                "waste_ratio": float(waste_ratio),
                "recommendation": (
                    "Consider adjusting part dimensions, batch quantity, "
                    "or sheet size to improve cut efficiency."
                )
            }
        })

    return suggestions

def suggest_cost_optimizations(bom: dict) -> list[dict]:
    suggestions = []

    summary = bom.get("summary", {})
    cutlists = bom.get("cutlists", {})

    material_cost = Decimal(str(summary.get("material_cost", 0)))
    waste_cost = Decimal(str(summary.get("waste_cost", 0)))

    if material_cost > 0:
        waste_ratio = waste_cost / material_cost

        if waste_ratio > Decimal("0.25"):
            suggestions.append({
                "type": "critical",
                "category": "material_waste",
                "message": "Excessive sheet wastage detected.",
                "recommendation": "Review part orientation, grain constraints, or increase batch size."
            })

    for material, cutlist in cutlists.items():
        if cutlist.get("total_waste_percent", 0) > 30:
            suggestions.append({
                "type": "info",
                "category": "cutlist",
                "message": f"{material}: inefficient nesting detected.",
                "recommendation": "Try alternate sheet size or relaxed grain rules."
            })

    return suggestions
