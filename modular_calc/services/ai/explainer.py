import re
from typing import List, Dict


RELATION_MAP = {
    ">=": "must be at least",
    "<=": "cannot exceed",
    "==": "must be equal to",
    ">": "must be greater than",
    "<": "must be less than",
}


def humanize_var(name: str) -> str:
    """Convert snake_case to readable label"""
    return name.replace("_", " ").strip()


def explain_candidates(candidates: List[Dict]) -> List[Dict]:
    explained = []

    for c in candidates:
        expr = c.get("expression", "").strip()
        confidence = c.get("confidence")

        explanation = "Constraint suggestion."

        # ----------------------------
        # Try relational parsing
        # ----------------------------
        for op, phrase in RELATION_MAP.items():
            if op in expr:
                lhs, rhs = expr.split(op, 1)
                explanation = (
                    f"{humanize_var(lhs)} {phrase} {humanize_var(rhs)}"
                )
                break

        explained.append({
            "expression": expr,
            "confidence": confidence,
            "explanation": f"💡 {explanation}.",
            "optimized": c.get("optimized", False),
            "source": c.get("source", "ai"),
        })

    return explained
