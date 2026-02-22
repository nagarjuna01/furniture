import os
import django
import json
import sys
from decimal import Decimal

# 1. SETUP DJANGO CONTEXT
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "furniture.settings")
django.setup()

from modular_calc.models import ModularProduct, PartTemplate
from material.models.wood import WoodMaterial
from django.utils import timezone

OUTPUT_FILE = "engine_wiring_report.json"

def audit_wiring():
    """
    Precision Audit: Maps Database Equation Requirements vs Engine Context Availability.
    This identifies the EXACT mismatch causing the KeyError.
    """
    report = {
        "timestamp": str(timezone.now()),
        "analysis": []
    }

    products = ModularProduct.objects.all()
    
    for product in products:
        product_node = {
            "product_id": str(product.id),
            "product_name": product.name,
            "validation_logic": product.product_validation_expression,
            "parts": []
        }

        # Simulate the "Context" the engine provides
        # These are the ONLY keys the code currently "wires"
        engine_provided_keys = [
            "length", "width", "height", 
            "product_length", "product_width", "product_height",
            "thickness", "t", "L", "W", "H"
        ]
        
        # Add product-specific parameters
        for param in product.parameters.all():
            engine_provided_keys.append(param.abbreviation)

        for pt in product.part_templates.all():
            # Extract variables used in the DB equations
            # We look for words that aren't numbers or math operators
            equations = [
                str(pt.part_length_equation),
                str(pt.part_width_equation),
                str(pt.part_qty_equation)
            ]
            
            used_variables = set()
            import re
            for eq in equations:
                # Find all alphanumeric words that start with a letter (potential variables)
                words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', eq)
                for word in words:
                    if word not in ['math', 'abs', 'max', 'min', 'None']:
                        used_variables.add(word)

            # Identify "Broken Wires" (Variables used in DB but not provided by Engine)
            missing_keys = [var for var in used_variables if var not in engine_provided_keys]

            part_node = {
                "part_name": pt.name,
                "part_id": str(pt.id),
                "equations": {
                    "L": pt.part_length_equation,
                    "W": pt.part_width_equation,
                    "Q": pt.part_qty_equation
                },
                "variables_demanded_by_db": list(used_variables),
                "missing_from_engine_context": missing_keys,
                "status": "CRITICAL_MISSING_WIRE" if missing_keys else "WIRED_CORRECTLY"
            }
            product_node["parts"].append(part_node)
            
        report["analysis"].append(product_node)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)
    
    print(f"✅ Audit Complete. Created {OUTPUT_FILE}")
    print(f"👉 Open this file and look for 'missing_from_engine_context'.")

if __name__ == "__main__":
    audit_wiring()