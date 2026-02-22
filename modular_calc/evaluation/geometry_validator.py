#modular_calc/evaluation/geometry_validator.py
from decimal import Decimal

class GeometryValidationError(ValueError):
    pass

class GeometryValidator:
    @staticmethod
    def validate_parts(parts: list[dict]):
        for idx, part in enumerate(parts, start=1):
            name = part.get("name", f"Part #{idx}")
            shape = part.get("shape_type", "RECT")

            # 1. Capture All Resolved Values
            # We use .get() defaults to 0 to avoid TypeErrors
            net_l = Decimal(str(part.get("net_length", 0)))
            net_w = Decimal(str(part.get("net_width", 0)))
            cut_l = Decimal(str(part.get("cut_length", 0)))
            cut_w = Decimal(str(part.get("cut_width", 0)))
            
            p1 = Decimal(str(part.get("p1", 0)))
            p2 = Decimal(str(part.get("p2", 0)))
            qty = Decimal(str(part.get("quantity", 0)))
            
            

            # 2. Finished (Net) Dimension Validation
            if net_l <= 0:
                raise GeometryValidationError(f"[{name}] Finished length must be > 0.")
            
            if shape != "CIRC" and net_w <= 0:
                raise GeometryValidationError(f"[{name}] Finished width must be > 0 for {shape}.")

            if qty <= 0:
                raise GeometryValidationError(f"[{name}] Quantity must be > 0.")

            # 3. Factory (Cut) Dimension Validation (THE IMPORTANT PART)
            # This catches cases where edgebands are thicker than the part itself
            if cut_l <= 0:
                raise GeometryValidationError(
                    f"[{name}] Edgeband thickness exceeds part length! (Wood cut would be {cut_l}mm)"
                )
            if shape != "CIRC" and cut_w <= 0:
                raise GeometryValidationError(
                    f"[{name}] Edgeband thickness exceeds part width! (Wood cut would be {cut_w}mm)"
                )

            # 4. Shape-Specific Parameter Validation
            if shape == "L_SHAPE":
                # Ensure the cutout (p1/p2) isn't larger than the actual wood we are cutting
                if p1 >= cut_l:
                    raise GeometryValidationError(f"[{name}] L-Shape cutout (p1: {p1}) exceeds available wood length ({cut_l}mm).")
                if p2 >= cut_w:
                    raise GeometryValidationError(f"[{name}] L-Shape cutout (p2: {p2}) exceeds available wood width ({cut_w}mm).")
            
            if shape == "CIRC":
                # For circles, P1 is often used as the inner radius (for a ring/donut shape)
                if p1 >= (cut_l / 2):
                    raise GeometryValidationError(f"[{name}] Inner radius (p1) cannot exceed the total radius.")