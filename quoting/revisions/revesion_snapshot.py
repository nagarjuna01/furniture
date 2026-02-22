from django.forms.models import model_to_dict
from decimal import Decimal

def build_quote_snapshot(quote):
    """
    Creates a full immutable snapshot. 
    Captures critical metadata (material names, hardware names) 
    to prevent data rot.
    """
    
    def serialize_val(val):
        """Standardize decimals/dates for JSON storage."""
        if isinstance(val, Decimal):
            return str(val)
        return val

    return {
        "id": quote.id,
        "quote_number": quote.quote_number,
        "total_sp": serialize_val(quote.total_sp),
        "tax_percentage": serialize_val(quote.tax_percentage),
        "shipping_charges": serialize_val(quote.shipping_charges),
        "solutions": [
            {
                "id": solution.id,
                "name": solution.name,
                "total_sp": serialize_val(solution.total_sp),
                "products": [
                    {
                        "id": product.id,
                        "product_name": product.product_template.name,
                        "qty": product.quantity,
                        "length": product.length_mm,
                        "width": product.width_mm,
                        "height": product.height_mm,
                        "total_sp": serialize_val(product.total_sp),
                        "parts": [
                            {
                                "id": part.id,
                                "part_name": part.part_name,
                                "material_name": part.material.name if part.material else "Unknown",
                                "qty": part.part_qty,
                                "length": part.length_mm,
                                "width": part.width_mm,
                                "total_sp": serialize_val(part.total_part_sp),
                                "hardware": [
                                    {
                                        "name": hw.hardware.name,
                                        "qty": hw.quantity,
                                        "total_sp": serialize_val(hw.total_sp)
                                    }
                                    for hw in part.hardware.all()
                                ]
                            }
                            for part in product.parts.all()
                        ]
                    }
                    for product in solution.products.all()
                ]
            }
            for solution in quote.solutions.all()
        ]
    }