# modular_calc/evaluation/geometry_utils.py

def generate_default_svg(shape_type, l, w, p1=0, p2=0):
    """
    Returns a standard SVG path string based on resolved dimensions.
    """
    try:
        # Convert to float for SVG coordinate safety
        l, w = float(l), float(w)
        p1, p2 = float(p1 or 0), float(p2 or 0)
        
        if shape_type == "RECT":
            return f"M 0 0 L {l} 0 L {l} {w} L 0 {w} Z"
        
        elif shape_type == "CIRC":
            r = l / 2
            return f"M 0 {r} a {r},{r} 0 1,0 {l},0 a {r},{r} 0 1,0 -{l},0"

        elif shape_type == "L_SHAPE":
            # Outer L shape: L and W are max bounds, p1/p2 are the 'inside' corner
            return f"M 0 0 L {l} 0 L {l} {p2} L {p1} {p2} L {p1} {w} L 0 {w} Z"
            
        elif shape_type == "U_SHAPE":
            # Back wall is L, legs are W, internal gap is p1
            side_leg = (l - p1) / 2
            return f"M 0 0 L {l} 0 L {l} {w} L {l-side_leg} {w} L {l-side_leg} {p2} L {side_leg} {p2} L {side_leg} {w} L 0 {w} Z"
            
    except (ValueError, TypeError):
        return ""
    return ""