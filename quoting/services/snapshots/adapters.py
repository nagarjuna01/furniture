# quoting/adapters.py
from decimal import Decimal

class EngineAdapter:
    """
    Translates Django Models into clean Dictionaries for the ProductEngine.
    """
    @staticmethod
    def to_engine_context(quote_product):
        """
        Gathers all DNA (Tenant Globals) and Product Specs.
        """
        # 1. Map Global Variables (DNA)
        # Using .values_list for performance to avoid model overhead
        globals_list = quote_product.tenant.global_variables.all().values_list('abbreviation', 'value')
        context = {abbr: float(val) for abbr, val in globals_list}

        # 2. Map Product Specs
        context.update({
            "L": float(quote_product.length_mm),
            "W": float(quote_product.width_mm),
            "H": float(quote_product.height_mm),
            "qty": int(quote_product.quantity),
        })

        # 3. Map Parameters (JSON field on QuoteProduct)
        if quote_product.parameters:
            context.update(quote_product.parameters)

        return context

    @staticmethod
    def from_engine_result(quote_product, result):
        """
        Translates Engine BOM output back into QuotePart objects.
        """
        parts_data = []
        for part in result.get("parts", []):
            parts_data.append({
                "quote_product": quote_product,
                "part_name": part["name"],
                "length_mm": Decimal(str(part["length"])),
                "width_mm": Decimal(str(part["width"])),
                "thickness": Decimal(str(part.get("thickness", 0))),
                "material_id": part.get("material_id"), # Resolved by engine
            })
        return parts_data