import sys
import os
import django
from decimal import Decimal
from asteval import Interpreter

# --- Django setup ---
sys.path.append(r"E:\Mrk_Furniture\furniture")  # adjust if needed
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "furniture.settings")
django.setup()

from modular_calc.models import PartTemplate

# --- Ask user for product dimensions ---
product_dims = {}
product_dims["product_length"] = float(input("Enter product length (mm): "))
product_dims["product_width"] = float(input("Enter product width (mm): "))
product_dims["product_height"] = float(input("Enter product height (mm): "))
product_dims["product_depth"] = float(input("Enter product depth (mm): "))

# --- Define parts with preset equations using part_thickness ---
parts_data = [
    {"name": "Side Panel", "length_eq": "product_height", "width_eq": "product_depth - part_thickness"},
    {"name": "Top Panel", "length_eq": "product_length - 2*part_thickness", "width_eq": "product_depth - part_thickness"},
    {"name": "Bottom Panel", "length_eq": "product_length - 2*part_thickness", "width_eq": "product_depth - part_thickness"},
    {"name": "Back Panel", "length_eq": "product_height - part_thickness", "width_eq": "product_length - 2*part_thickness"},
    {"name": "Door Left", "length_eq": "product_height / 2", "width_eq": "(product_width - part_thickness) / 2"},
    {"name": "Door Right", "length_eq": "product_height / 2", "width_eq": "(product_width - part_thickness) / 2"},
    {"name": "Drawer Front", "length_eq": "product_width / 3", "width_eq": "product_height / 4"},
    {"name": "Drawer Side Left", "length_eq": "(product_height / 4) - part_thickness", "width_eq": "(product_depth / 2) - part_thickness"},
    {"name": "Drawer Side Right", "length_eq": "(product_height / 4) - part_thickness", "width_eq": "(product_depth / 2) - part_thickness"},
    {"name": "Drawer Bottom", "length_eq": "(product_width / 3) - part_thickness", "width_eq": "(product_depth / 2) - part_thickness"},
]

# --- Ask user for thickness and quantity per part ---
for part in parts_data:
    part["thickness"] = float(input(f"Enter thickness for {part['name']} (mm): "))
    part["quantity"] = int(input(f"Enter quantity for {part['name']}: "))

# --- Evaluate parts ---
def evaluate_part(part_template, product_dims):
    aeval = Interpreter()
    context = {**product_dims, "part_thickness": part_template["thickness"]}
    aeval.symtable.update(context)
    
    try:
        length = float(aeval(part_template["length_eq"]))
        width = float(aeval(part_template["width_eq"]))
        quantity = int(part_template["quantity"])
        area_mm2 = length * width * quantity
        return {
            "length": length,
            "width": width,
            "quantity": quantity,
            "area_mm2": area_mm2
        }
    except Exception as e:
        return {"error": str(e)}

# --- Print results ---
for part in parts_data:
    result = evaluate_part(part, product_dims)
    print(f"{part['name']}: {result}")
