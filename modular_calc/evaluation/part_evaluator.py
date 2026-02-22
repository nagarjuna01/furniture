from typing import Dict, List, Optional, Any
from decimal import Decimal
from .context import ExpressionContext, to_decimal
from material.services.unit_conversion import MeasurementUnit,UnitConversionService
class PartEvaluator:
    """
    Evaluates a single PartTemplate within a product context.
    Handles cross-part variable resolution (e.g., rdfacia_thickness).
    """

    def __init__(
        self, 
        part_template, 
        product_dims: Dict[str, Decimal], 
        parameters: Dict[str, Decimal], 
        material_obj: Optional[Any] = None,
        all_templates: Optional[List[Any]] = None  # Added to fix TypeError
    ):
        self.part_template = part_template
        self.product_dims = product_dims
        self.parameters = parameters
        self.material_obj = material_obj
        self.all_templates = all_templates or []

    def _get_context(self) -> Dict[str, Any]:
        context = {k: float(v) for k, v in self.product_dims.items()}
        context.update({k: float(v) for k, v in self.parameters.items()})

        # Helper to resolve thickness to MM using your service
        def resolve_to_mm(obj):
            if not obj or not obj.thickness_value:
                return 0.0
            # If already MM, return float to save a DB hit/service call
            if obj.thickness_unit and obj.thickness_unit.code == "MM":
                return float(obj.thickness_value)
            
            # Fallback to service for non-MM units
            try:
                mm_unit = MeasurementUnit.objects.get(code="MM")
                return float(UnitConversionService.convert(
                    value=obj.thickness_value, 
                    from_unit=obj.thickness_unit, 
                    to_unit=mm_unit
                ))
            except:
                return float(obj.thickness_value)

        # 1. Current Part Thickness
        if self.material_obj:
            val = resolve_to_mm(self.material_obj)
            context["material_thickness"] = val
            context["thickness"] = val

        # 2. Cross-Part Thickness (The 'side_thickness' fix)
        for template in self.all_templates:
            prefix = template.name.lower().replace(" ", "").replace("-", "_")
            # Find the default material from the whitelist (using the correct model name)
            mat_link = template.partmaterialwhitelist_set.filter(is_default=True).first()
            if mat_link and mat_link.material:
                context[f"{prefix}_thickness"] = resolve_to_mm(mat_link.material)

        return context

    def evaluate(self) -> Dict[str, Any]:
        """
        Executes equations for length, width, and quantity.
        """
        ctx_data = self._get_context()
        expr_ctx = ExpressionContext(ctx_data)

        # Evaluate core dimensions
        length = expr_ctx.evaluate(self.part_template.length_equation or "0")
        width = expr_ctx.evaluate(self.part_template.width_equation or "0")
        quantity = expr_ctx.evaluate(self.part_template.quantity_equation)

        return {
            "template_id": self.part_template.id,
            "name": self.part_template.name,
            "length": float(length),
            "width": float(width),
            "quantity": float(quantity),
            "thickness": ctx_data.get("thickness", 0),
            "context_snapshot": ctx_data # Useful for debugging equations
        }
class ProductionOrchestrator:
    """
    SaaS Logic Layer: Processes a list of part templates for a specific product.
    Ensures that Part A's results are available to Part B's formulas.
    """
    def __init__(self, product_dims: Dict, parameters: Dict):
        self.product_dims = product_dims
        self.parameters = parameters
        self.global_results = {}

    def calculate_bill_of_materials(self, part_templates: List[Any]) -> List[Dict]:
        bom = []
        # Optimization: Prefetch all thicknesses once
        # thickness_map = { 'rdfacia': 18.0, ... }
        
        for template in part_templates:
            evaluator = PartEvaluator(
                part_template=template,
                product_dims=self.product_dims,
                parameters={**self.parameters, **self.global_results}, # Merge results
                material_obj=getattr(template, 'material', None)
            )
            
            result = evaluator.evaluate()
            
            # Injection logic
            safe_name = template.name.lower().replace(" ", "_").replace("-", "_")
            self.global_results[f"{safe_name}_thickness"] = result.get('thickness', 0)
            
            bom.append(result)
        return bom