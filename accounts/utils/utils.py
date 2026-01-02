import re
from decimal import Decimal

def evaluate_parametric_equation(equation, system_vars, global_vars, part_material_thickness=None):
    """
    equation: "W - (2 * @ST)" or "H - @TK - part_thickness"
    system_vars: {'W': 600, 'H': 720, 'D': 560}
    global_vars: {'@ST': 18.0, '@BT': 9.0, '@TK': 100.0}
    part_material_thickness: 25.0 (If a custom material is picked)
    """
    # 1. Start with System Variables
    context = {k: str(v) for k, v in system_vars.items()}
    
    # 2. Add Global Variables
    context.update({k: str(v) for k, v in global_vars.items()})
    
    # 3. Handle 'part_thickness' (The Source of Truth Override)
    # If a salesperson picked a 25mm material, 'part_thickness' 
    # in the equation will use 25.0 instead of the global @ST.
    if part_material_thickness is not None:
        context['part_thickness'] = str(part_material_thickness)
    
    # 4. Resolve the equation string
    # Sort by length to avoid @ST matching @ST_OFFSET partially
    sorted_keys = sorted(context.keys(), key=len, reverse=True)
    
    resolved_eq = str(equation)
    for key in sorted_keys:
        resolved_eq = resolved_eq.replace(key, context[key])
    
    # 5. Safe evaluate (using eval for simple math, or a math parser)
    try:
        # We use a limited scope for security
        return eval(resolved_eq, {"__builtins__": None}, {})
    except Exception as e:
        return f"Error in equation: {e}"