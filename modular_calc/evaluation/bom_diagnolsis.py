from typing import Dict, List
from .bom_builder import BOMBuilder

class EngineDebugger:
    """
    Analyzes a Product and its Engine state to find why outputs are zero.
    """
    def __init__(self, product, product_dims: Dict, material_selections: Dict):
        self.product = product
        self.product_dims = product_dims
        self.material_selections = material_selections

    def analyze(self) -> List[str]:
        issues = []
        
        # 1. Check Part Templates
        templates = self.product.parts.all()
        if not templates.exists():
            issues.append(f"Product '{self.product.name}' has NO Part Templates defined.")
        
        # 2. Check Whitelists & Materials
        for template in templates:
            m_id = self.material_selections.get(str(template.id))
            whitelist = template.material_whitelist.all()
            
            if not whitelist.exists():
                issues.append(f"Part '{template.name}' has no material whitelist.")
            
            default_material = template.material_whitelist.filter(is_default=True).first()
            if not m_id and not default_material:
                issues.append(f"Part '{template.name}' has no default material and none was selected.")

        # 3. Check Dimensions
        for dim, val in self.product_dims.items():
            if val <= 0:
                issues.append(f"Dimension '{dim}' is {val}. Parts may be skipped due to zero/negative size.")

        return issues

def get_diagnostic_report(product, dims, selections):
    debugger = EngineDebugger(product, dims, selections)
    return debugger.analyze()