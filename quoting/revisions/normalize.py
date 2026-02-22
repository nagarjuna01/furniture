# Updated normalization with safety checks
def normalize_snapshot(snapshot):
    normalized = {
        "totals": {
            "total_cp": snapshot.get("total_cp", 0),
            "total_sp": snapshot.get("total_sp", 0),
            "grand_total": snapshot.get("grand_total", 0),
        },
        "products": {}
    }

    for sol in snapshot.get("solutions", []):
        for p in sol.get("products", []):
            p_id = str(p.get("id", p.get("product"))) # Fallback to name if ID missing
            normalized["products"][p_id] = {
                "name": p["product"],
                "qty": p["quantity"],
                "total_sp": p["total_sp"],
                "dimensions": p.get("dimensions", {}),
                "parts": {
                    str(part.get("id", part["part"])): {
                        "name": part["part"],
                        "material": part["material"],
                        "qty": part["quantity"],
                        "total_sp": part["total_sp"],
                    } for part in p.get("parts", [])
                }
            }
    return normalized