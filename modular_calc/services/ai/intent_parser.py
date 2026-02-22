import re

RELATION_MAP = {
    "shorter than": "<=",
    "longer than": ">=",
    "at least": ">=",
    "at most": "<=",
    "less than": "<=",
    "greater than": ">=",
}

KNOWN_PARTS = {
    "apron": "apron_length",
    "panel": "panel_length",
    "door": "door_length",
    "shelf": "shelf_length",
    "product": "product_length",
}

RELATION_OP_MAP = {
    "<": "Lt",
    "<=": "LtE",
    ">": "Gt",
    ">=": "GtE",
}


def parse_intent(text: str) -> dict:
    """
    Convert natural language into a structured intent.
    Deterministic + auditable.
    """

    text = text.lower()

    intent = {
        "relation": None,      # raw symbol
        "op": None,            # canonical engine operator
        "lhs": None,
        "rhs": None,
        "offset": "0",
        "raw_text": text,
    }

    # ----------------------------
    # 1️⃣ Relation detection
    # ----------------------------
    for phrase, rel in RELATION_MAP.items():
        if phrase in text:
            intent["relation"] = rel
            intent["op"] = RELATION_OP_MAP.get(rel)
            break

    # ----------------------------
    # 2️⃣ Offset detection
    # ----------------------------
    match = re.search(r"(-?\d+(\.\d+)?)", text)
    if match:
        intent["offset"] = match.group(1)

    # ----------------------------
    # 3️⃣ LHS / RHS detection
    # ----------------------------
    for word, key in KNOWN_PARTS.items():
        if word in text:
            if not intent["lhs"]:
                intent["lhs"] = key
            elif not intent["rhs"] and key != intent["lhs"]:
                intent["rhs"] = key

    return intent
