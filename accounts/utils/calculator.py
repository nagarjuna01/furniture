from accounts.models.globalvariables import GlobalVariable
import re

def resolve_variables(equation, global_vars_dict, system_vars):
    """
    equation: "H - (2 * @ST)"
    global_vars_dict: {"@ST": 18, "@BT": 9}
    system_vars: {"H": 720, "W": 600}
    """
    # 1. Combine all available variables
    # System variables (H, W, D) + Global Variables (@ST, @BT)
    all_vars = {**system_vars, **global_vars_dict}
    
    # 2. Replace abbreviations with values (Sort by length to avoid partial replacement)
    sorted_keys = sorted(all_vars.keys(), key=len, reverse=True)
    
    resolved_eq = str(equation)
    for key in sorted_keys:
        resolved_eq = resolved_eq.replace(key, str(all_vars[key]))
        
    return resolved_eq

def get_resolved_equation(equation_str, tenant):
    """
    Replaces abbreviations like @ST with their decimal values 
    for a specific tenant.
    """
    # 1. Fetch all variables for this tenant
    variables = GlobalVariable.objects.filter(tenant=tenant)
    var_dict = {v.abbr: str(v.value) for v in variables}
    
    # 2. Sort keys by length (descending) to prevent partial matching 
    # (e.g., @ST and @ST_EXTRA)
    sorted_abbrs = sorted(var_dict.keys(), key=len, reverse=True)
    
    resolved_eq = equation_str
    for abbr in sorted_abbrs:
        if abbr in resolved_eq:
            resolved_eq = resolved_eq.replace(abbr, var_dict[abbr])
            
    return resolved_eq

def get_tenant_variable_map(tenant):
    """
    Returns a clean dictionary of {@abbr: value} for math.
    Result: {'@ST': 18.00, '@BT': 9.00, ...}
    """
    variables = GlobalVariable.objects.filter(tenant=tenant)
    return {v.abbr: float(v.value) for v in variables}