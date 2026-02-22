def suggest_fixes(violations: list[dict]) -> list[str]:
    suggestions = []

    for v in violations:
        var_name = v["lhs"].replace("_", " ").title()
        required = v["required"]
        actual = v["actual"]
        op = v["op"]

        if op in ("Lt", "LtE"):
            suggestions.append(
                f"Reduce {var_name} from {actual}mm to {required}mm or below."
            )
        elif op in ("Gt", "GtE"):
            suggestions.append(
                f"Increase {var_name} from {actual}mm to at least {required}mm."
            )
        elif op == "Eq":
            suggestions.append(
                f"Set {var_name} exactly to {required}mm."
            )

    return suggestions

from .rule_parser import parse_constraints
from .range_solver import solve_ranges
from .violation_analyzer import analyze_violations
from .suggestion_engine import suggest_fixes

def solve_constraints(expr: str, context: dict, target_var: str):
    # 1️⃣ Parse once
    constraints = parse_constraints(expr)

    # 2️⃣ Solve allowed ranges
    ranges = solve_ranges(constraints, target_var, context)

    # 3️⃣ Analyze violations per constraint
    violations = analyze_violations(constraints, context)

    # 4️⃣ Generate fixes
    suggestions = suggest_fixes(violations)

    return {
        "ranges": ranges,
        "violations": violations,
        "suggestions": suggestions
    }
