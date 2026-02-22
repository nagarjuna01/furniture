# modular_calc/services/ai/expression_suggestion.py

from .intent_parser import parse_intent
from .candidate_generator import generate_candidates
from .candidate_filter import filter_candidates
from .optimizer import optimize_candidates
from .explainer import explain_candidates


def suggest_expression(intent: str, context):
    structured = parse_intent(intent)

    candidates = generate_candidates(structured, context)

    if not candidates:
        return []

    valid = filter_candidates(candidates, context)

    # ----------------------------
    # Fallback (safe draft)
    # ----------------------------
    if not valid:
        fallback = candidates[0]
        return [{
            "expression": fallback.get("expression", ""),
            "confidence": fallback.get("confidence", 0.4),
            "explanation": (
                "⚠️ Draft rule generated. "
                "Please review before applying."
            ),
            "status": "draft",
            "optimized": False,
            "source": "ai",
            "safe_to_apply": False,
        }]

    # ----------------------------
    # Optimized & explained
    # ----------------------------
    optimized = optimize_candidates(valid, context)
    explained = explain_candidates(optimized)

    # Final safety tagging
    for e in explained:
        e.setdefault("status", "validated")
        e.setdefault("safe_to_apply", True)

    return explained
