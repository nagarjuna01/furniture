# utils/expression_validation.py
from .safe_eval import safe_eval
import ast
import re
def validate_boolean_expression(expr: str, context: dict):
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ValueError({
            "error": "Syntax error",
            "token": e.text.strip() if e.text else None,
            "position": e.offset,
        })

    # Run evaluation
    try:
        result = safe_eval(expr, context)
    except NameError as e:
        token = str(e).split("'")[1]
        raise ValueError({
            "error": "Unknown variable",
            "token": token,
        })

    if not isinstance(result, bool):
        raise ValueError({
            "error": "Expression must return boolean",
        })

    return True



def validate_template_completion(expression: str) -> bool:
    """
    Check if any {bracketed_placeholders} remain in the expression.
    """
    # Regex to find remaining {tags}
    remaining = re.findall(r'\{(\w+)\}', expression)
    if remaining:
        # The AI Agent can now say: "You forgot to define the {gap} variable!"
        return False, remaining
    return True, []