from decimal import Decimal
from typing import Dict, Any, Optional

def to_decimal(value: Any) -> Decimal:
    """Helper to ensure precision for geometric calculations."""
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (ValueError, TypeError):
        return Decimal("0")

class ProductContext:
    """
    Tier 5 Stateful Context:
    Maintains Decimal precision for all variables. Allows for recursive 
    parameter updates where one part's calculated dimensions become 
    variables for the next part.
    """

    def __init__(self, product_dims: Dict[str, Any], parameters: Optional[Dict[str, Any]] = None):
        # Base variables (Cabinet_Width, etc.)
        self.ctx: Dict[str, Any] = {
            "product_length": to_decimal(product_dims.get("product_length") or product_dims.get("length", 0)),
            "product_width": to_decimal(product_dims.get("product_width") or product_dims.get("width", 0)),
            "product_height": to_decimal(product_dims.get("product_height") or product_dims.get("height", 0)),
            "quantity": to_decimal(product_dims.get("quantity")),
        }
        
        # Sorthand Aliases
        self.ctx.update({
            "L": self.ctx["product_length"],
            "W": self.ctx["product_width"],
            "H": self.ctx["product_height"],
            "Q": self.ctx["quantity"]
        })

        # Load global parameters (e.g., SKIRTING_HEIGHT)
        if parameters:
            for k, v in parameters.items():
                # IMPROVEMENT: Use the key exactly as defined by abbreviation, 
                # but also provide a lowercase version to be "user-friendly"
                val = to_decimal(v)
                clean_key = k.replace(" ", "_")
                
                # Store original (usually Uppercase from your JS)
                self.ctx[clean_key] = val
                
                # Store lowercase fallback if different
                if clean_key.lower() != clean_key:
                    self.ctx[clean_key.lower()] = val
        
    def inject_material_props(self, part_name: str, material: Any) -> None:
        """
        Required by PartEvaluator.
        Injects material-specific properties into the context using a material object.
        """
        if not material:
            return

        clean_name = part_name.lower().replace(" ", "_")
        # Extract thickness safely
        thickness = to_decimal(getattr(material, "thickness_mm", 
                               getattr(material, "thickness_value", 0)))
        
        # Standard key used in formulas: side_panel_thickness
        self.ctx[f"{clean_name}_thickness"] = thickness
        
        # Semantic Alias (e.g., if any side is found, set global side_thickness)
        if "side" in clean_name:
            self.ctx["side_thickness"] = thickness
            
        # Store metadata
        self.ctx[f"{clean_name}_material_name"] = getattr(material, "name", "Unknown")

    def inject_material_thickness(self, part_name: str, thickness: Any) -> None:
        """Helper for direct thickness injection."""
        clean_name = part_name.lower().replace(" ", "_")
        self.ctx[f"{clean_name}_thickness"] = to_decimal(thickness)
        if "side" in clean_name:
            self.ctx["side_thickness"] = to_decimal(thickness)

    def update_calculated_part(self, part_name: str, length: Any, width: Any, thickness: Optional[Any] = None) -> None:
        """
        Updates context with finished part dimensions for recursive reference.
        Enables: 'top_width = side_panel_length + 20'
        """
        clean_name = part_name.lower().replace(" ", "_")
        self.ctx[f"{clean_name}_length"] = to_decimal(length)
        self.ctx[f"{clean_name}_width"] = to_decimal(width)
        if thickness is not None:
            self.ctx[f"{clean_name}_thickness"] = to_decimal(thickness)

    def get_context(self) -> Dict[str, Any]:
        """Returns the dictionary for eval()."""
        return self.ctx

import math
from decimal import Decimal
from typing import Dict, Any, Optional

class ExpressionContext:
    """
    The Execution Engine for formulas.
    It takes the variables from ProductContext and runs the math.
    """

    def __init__(self, context_data: Dict[str, Any]):
        """
        Initializes the engine with a dictionary of variables (H, W, D, etc.)
        Values are converted to float for evaluation to ensure compatibility 
        with standard Python math operators.
        """
        self.context = {}
        for k, v in context_data.items():
            if isinstance(v, (Decimal, int, float)):
                self.context[k] = float(v)
            else:
                self.context[k] = v

        # Add standard safe math functions to the environment
        self.context.update({
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "ceil": math.ceil,
            "floor": math.floor,
            "sqrt": math.sqrt,
            "pow": pow,
        })

    def evaluate(self, expression: str) -> Decimal:
        """
        The core function called by PartEvaluator and validators.
        Turns "H - 20" into a Decimal value.
        """
        if not expression or str(expression).strip() == "":
            return Decimal("0")

        try:
            # Restricted eval: No access to system builtins (__import__, etc.)
            # only uses the context we provided.
            result = eval(
                str(expression), 
                {"__builtins__": {}}, 
                self.context
            )
            
            # Convert back to Decimal for the high-precision SaaS core
            return Decimal(str(result)).quantize(Decimal("0.0001"))
            
        except NameError as e:
            # Specific error for when a variable (like SIDE_L) is missing
            raise NameError(f"Missing variable in formula: {e}")
        except Exception as e:
            # General math or syntax errors
            raise ValueError(f"Calculation Error in '{expression}': {e}")

    def update_context(self, key: str, value: Any):
        """
        Updates the engine's memory mid-calculation.
        Crucial for solving the 'Sequential Issue'.
        """
        self.context[key] = float(value)