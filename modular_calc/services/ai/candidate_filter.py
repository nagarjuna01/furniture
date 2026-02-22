import logging
from modular_calc.utils.expression_validation import validate_boolean_expression

logger = logging.getLogger("modular_calc.rules")


def filter_candidates(
    candidates: list[dict],
    context: dict,
    *,
    strict: bool = False
) -> tuple[list[dict], list[dict]]:
    """
    Filters candidates based on boolean expressions.

    Returns:
        valid_candidates: rules that passed
        rejected_candidates: rules that failed with reasons
    """

    valid = []
    rejected = []

    for c in candidates:
        expr = c.get("expression")

        # No rule = always valid
        if not expr:
            valid.append(c)
            continue

        try:
            result = validate_boolean_expression(expr, context)

            if result is True:
                valid.append(c)
            else:
                rejected.append({
                    **c,
                    "failure_reason": "expression_evaluated_false",
                    "expression": expr,
                })

        except NameError as e:
            reason = f"missing_variable: {str(e)}"
            logger.warning(f"Rule skipped: {reason} | expr={expr}")

            rejected.append({
                **c,
                "failure_reason": reason,
                "expression": expr,
            })

            if strict:
                raise

        except SyntaxError as e:
            reason = f"syntax_error: {str(e)}"
            logger.error(f"Invalid rule syntax | expr={expr}")

            rejected.append({
                **c,
                "failure_reason": reason,
                "expression": expr,
            })

            if strict:
                raise

        except Exception as e:
            reason = f"runtime_error: {str(e)}"
            logger.exception(f"Rule evaluation crashed | expr={expr}")

            rejected.append({
                **c,
                "failure_reason": reason,
                "expression": expr,
            })

            if strict:
                raise

    return valid, rejected
