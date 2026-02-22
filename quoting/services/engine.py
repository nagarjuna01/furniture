# quoting/services/product_service.py
from decimal import Decimal
from accounts.models import GlobalVariable
from rest_framework.exceptions import ValidationError

class QuoteProductService:
    @staticmethod
    def build_context(qp):
        # Fetch DNA (Globals)
        globals_map = {
            v.abbr: float(v.value)
            for v in GlobalVariable.objects.filter(tenant=qp.tenant)
        }
        
        ctx = {
            "product_length": float(qp.length_mm),
            "product_width": float(qp.width_mm),
            "product_height": float(qp.height_mm),
            "quantity": qp.quantity,
        }
        ctx.update(globals_map)
        
        # FACTORY DNA LOGIC: 
        # Instead of manual 15% increase, we pass 'ST' to the engine.
        # The Engine formulas (e.g. "Part.Thickness = @ST") do the work.
        return ctx
    def apply_factory_dna_surcharge(qp):
        """
        Production-ready: Applies adjustment as a metadata-backed field.
        """
        st_val = qp.tenant.global_variables.filter(abbr='ST').values_list('value', flat=True).first()
        
        if st_val and Decimal(st_val) > 18:
            # We don't just multiply; we record the factor
            qp.adjustment_factor = Decimal('1.15')
            qp.adjustment_reason = "Factory DNA: Shelf Thickness Surcharge (@ST > 18mm)"
            
            # The recalc_quote_product service should handle: 
            # final_sp = (sum_of_parts + hardware) * adjustment_factor
            return True
        return False

# quoting/services/engine.py

def validate_product_bounds(qp, room_dimensions):
    """
    Ensures the product physically fits in the assigned 3D space.
    """
    # Simple Bounding Box check
    if (qp.pos_x + qp.width_mm > room_dimensions.width or
        qp.pos_z + qp.length_mm > room_dimensions.depth):
        raise ValidationError({
            "geometry": "Product exceeds room boundaries. Collision detected."
        })
    return True