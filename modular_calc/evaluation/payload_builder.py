# modular_calc/evaluation/payload_builder.py

class ProductPayloadBuilder:
    def __init__(self, product, product_dims, parameters, quantities):
        self.product = product
        self.product_dims = product_dims
        self.parameters = parameters or {}  # From request
        self.quantities = quantities

    def build(self) -> dict:
        # 1. Fetch defaults from the database
        resolved_params = {}
        # Assuming the related name on ModularProduct is 'parameters'
        for param in self.product.parameters.all():
            # Use abbreviation (e.g., 'D1FH') as the key for the eval scope
            # Replace spaces with underscores for Python variable compatibility
            key = param.abbreviation.strip().replace(" ", "_")
            resolved_params[key] = param.default_value
        
        # 2. Merge: Request data overrides database defaults
        final_params = {**resolved_params, **self.parameters}
        
        # DEBUG: Verify D1FH is present here
        print(f"DEBUG BUILDER: Final keys: {list(final_params.keys())}")
        print("PRODUCT TYPE:", type(self.product))
        print("HAS PARAMETERS ATTR:", hasattr(self.product, "parameters"))
        return {
            "product": self.product,
            "product_name": self.product.name,
            "category": self.product.category.name if self.product.category else None,
            "product_dims": self.product_dims,
            "parameters": final_params,  # Now contains {'D1FH': 150.00, ...}
            "quantities": self.quantities,
            "part_templates": list(
                self.product.part_templates.select_related("default_material").all()
            ),
            "hardware_rules": list(self.product.hardware_rules.all()),
        }