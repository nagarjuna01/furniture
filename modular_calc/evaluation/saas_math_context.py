import re
from typing import Dict, Any, List
from django.db.models import Model

class SaaSMathContext:
    """
    Tier 5: The engine that gathers all variables (Global, Product, and Part-level)
    into a single context for the DRF calculation endpoints.
    """
    
    def __init__(self, tenant_settings: Dict[str, Any], product_instance: Model):
        self.tenant_settings = tenant_settings
        self.product = product_instance
        self.base_context = {}

    def build_global_context(self) -> Dict[str, float]:
        """
        Gathers tenant-wide constants (e.g., standard gaps, default thicknesses).
        """
        # Example: Tenant-level 'global_scribe' = 20.0
        return {k: float(v) for k, v in self.tenant_settings.items()}

    def build_product_context(self) -> Dict[str, float]:
        """
        Extracts product dimensions (height, width, depth).
        """
        return {
            "product_height": float(self.product.height),
            "product_width": float(self.product.width),
            "product_length": float(self.product.length),
        }

    def build_dynamic_part_thicknesses(self) -> Dict[str, float]:
        """
        Automatically turns every Part Name into a '{name}_thickness' variable.
        This prevents 'carpenter work' by making the engine self-aware.
        """
        thickness_map = {}
        # Assuming product.parts is a related manager
        for part in self.product.parts.all():
            clean_name = re.sub(r'[^a-zA-Z0-9]', '', part.name).lower()
            # Link to the actual material thickness of that specific part
            thickness_map[f"{clean_name}_thickness"] = float(part.material.thickness_mm)
        return thickness_map

    def get_full_context(self) -> Dict[str, Any]:
        """Combines everything for the final evaluator."""
        ctx = {}
        ctx.update(self.build_global_context())
        ctx.update(self.build_product_context())
        ctx.update(self.build_dynamic_part_thicknesses())
        # Standard math helpers
        ctx.update({"abs": abs, "min": min, "max": max, "round": round})
        return ctx