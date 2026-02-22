from decimal import Decimal
from typing import List, Dict

ALLOWED_RELATIONS = {">", ">=", "<", "<=", "=="}


def generate_candidates(intent: dict, ctx: dict) -> List[Dict]:
    """
    AI-adjacent deterministic candidate generator.
    NEVER evaluates expressions.
    NEVER mutates context.
    """

    lhs = intent.get("lhs")
    rhs = intent.get("rhs")
    rel = intent.get("relation")
    offset = intent.get("offset", "0")

    candidates: List[Dict] = []

    # ----------------------------
    # Strict intent validation
    # ----------------------------
    if not lhs or not rhs or not rel:
        return []

    if rel not in ALLOWED_RELATIONS:
        return []

    if lhs not in ctx or rhs not in ctx:
        return []

    try:
        offset_val = Decimal(str(offset))
    except Exception:
        return []

    # ----------------------------
    # Candidate 1: direct relation
    # ----------------------------
    candidates.append({
        "expression": f"{lhs} {rel} {rhs} - {offset_val}",
        "confidence": Decimal("0.90"),
        "explanation": (
            f"Ensures {lhs} satisfies {rel} relation against "
            f"{rhs} with offset {offset_val}"
        ),
        "source": "ai",
        "intent_signature": f"{lhs}:{rel}:{rhs}:{offset_val}",
    })

    # ----------------------------
    # Candidate 2: normalized form
    # ----------------------------
    candidates.append({
        "expression": f"{rhs} - {lhs} >= {offset_val}",
        "confidence": Decimal("0.70"),
        "explanation": (
            f"Normalized inequality ensuring difference between "
            f"{rhs} and {lhs} meets offset"
        ),
        "source": "ai",
        "intent_signature": f"{rhs}-lhs>={offset_val}",
    })

    return candidates
