from decimal import Decimal
import operator
from modular_calc.utils.safe_eval import safe_eval
from modular_calc.services.constraints.rule_parser import parse_constraints

OPERATORS = {
    "Gt": operator.gt,
    "GtE": operator.ge,
    "Lt": operator.lt,
    "LtE": operator.le,
    "Eq": operator.eq,
    "NotEq": operator.ne,
}

def analyze_violations(expr: str, context: dict) -> list[dict]:
    """
    Evaluates constraints and returns structured violations.
    This is the ONLY truth source for suggestion + UI + AI layers.
    """
    constraints = parse_constraints(expr)
    failures = []

    for c in constraints:
        lhs = c["lhs"]
        op = c["op"]
        rhs_expr = c["rhs"]

        # 1️⃣ Resolve actual value
        actual_val = context.get(lhs)
        if actual_val is None:
            continue

        # 2️⃣ Resolve RHS safely
        try:
            rhs_val = safe_eval(rhs_expr, context)
        except Exception:
            continue

        # 3️⃣ Compare
        op_func = OPERATORS.get(op)
        if not op_func:
            continue

        try:
            actual_dec = Decimal(str(actual_val))
            required_dec = Decimal(str(rhs_val))

            if not op_func(actual_dec, required_dec):
                failures.append({
                    "lhs": lhs,
                    "op": op,
                    "rhs": rhs_expr,
                    "actual": actual_dec,
                    "required": required_dec,
                })

        except Exception:
            continue

    return failures
