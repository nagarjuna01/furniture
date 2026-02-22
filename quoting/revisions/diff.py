def diff_dict(old, new):
    added = {}
    removed = {}
    changed = {}

    for key in new:
        if key not in old:
            added[key] = new[key]
        elif new[key] != old[key]:
            changed[key] = {
                "from": old[key],
                "to": new[key],
            }

    for key in old:
        if key not in new:
            removed[key] = old[key]

    return added, removed, changed

def diff_revisions(old_snap, new_snap):
    """
    Analyzes differences between two quote snapshots.
    Assumes snapshots are structured as: {"products": {"prod_id": {...}, ...}}
    """
    diff = {
        "header": {},
        "products": {"added": {}, "removed": {}, "changed": {}}
    }

    # 1. Compare Header Stats (Total SP, Tax, etc.)
    for field in ["total_sp", "grand_total", "tax_amount"]:
        old_val = old_snap.get(field)
        new_val = new_snap.get(field)
        if old_val != new_val:
            diff["header"][field] = {"from": old_val, "to": new_val}

    # 2. Compare Products
    added, removed, changed = diff_dict(
        old_snap.get("products", {}),
        new_snap.get("products", {}),
    )

    diff["products"]["added"] = added
    diff["products"]["removed"] = removed

    for pid, change in changed.items():
        old_p = change["from"]
        new_p = change["to"]

        # Deep diff for dimensions and quantity
        p_diff = {}
        for attr in ["qty", "total_sp", "L", "W", "H"]:
            if old_p.get(attr) != new_p.get(attr):
                p_diff[attr] = {"from": old_p.get(attr), "to": new_p.get(attr)}

        # Nested Diff for Parts (Cylinder level)
        pa, pr, pc = diff_dict(old_p.get("parts", {}), new_p.get("parts", {}))
        if pa or pr or pc:
            p_diff["parts"] = {"added": pa, "removed": pr, "changed": pc}

        diff["products"]["changed"][pid] = p_diff

    return diff
