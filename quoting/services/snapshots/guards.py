from django.core.exceptions import ValidationError

class ProductGuard:
    """
    Feasibility checks for Modular Products.
    """
    @staticmethod
    def check_physical_limits(qp):
        """Ensures dimensions are within factory machine capabilities."""
        template = qp.product_template
        
        # 1. Max/Min Dimension Guards
        if qp.length_mm > template.max_length:
            raise ValidationError(f"Length {qp.length_mm} exceeds machine limit of {template.max_length}")
        
        if qp.width_mm < template.min_width:
            raise ValidationError(f"Width {qp.width_mm} is below minimum requirement.")

    @staticmethod
    def check_material_compatibility(qp):
        """Ensures selected finish is available for the product type."""
        # e.g., Cannot use 1mm Edgebanding on 12mm glass-filled panels
        pass

class QuoteGuard:
    """
    Business logic and Financial safety.
    """
    @staticmethod
    def check_margin_safety(quote):
        """Prevents the 'Silent Killer' of selling below cost."""
        if quote.total_sp < quote.total_cp:
            raise ValidationError("Critical Error: Selling price is lower than cost price.")

    @staticmethod
    def check_lock_status(quote):
        """Prevents mutation of historical data."""
        if quote.status == "locked":
            raise ValidationError("This quote is locked and cannot be modified.")