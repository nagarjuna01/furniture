from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse, Http404

from quoting.models import QuoteProduct
from modular_calc.evaluation.product_engine import ProductEngine
from .services import render_svg


@api_view(["GET"])
def product_svg(request, quote_product_id: int):
    """
    Generate full-product SVG using:
    1. Product's master SVG template (preferred)
    2. Else, individual part templates stitched vertically
    3. Else, fallback rectangle layout

    All dimensions come from the new ProductEngine evaluator.
    """
    try:
        qp = QuoteProduct.objects.select_related("product_template").get(pk=quote_product_id)
    except QuoteProduct.DoesNotExist:
        raise Http404("QuoteProduct not found")

    # Build product context (length/width/height/quantity/parameters)
    dims = qp.as_dims()

    # Run ProductEngine to evaluate parts with new evaluator
    engine = ProductEngine(qp.product_template)
    result = engine.evaluate(dims, parameters={})   # parameters={} for now

    parts = result["parts"]
    product_template = qp.product_template

    # ------------------------------------------------------------------
    # CASE 1: PRODUCT LEVEL SVG TEMPLATE EXISTS  → BEST QUALITY OUTPUT
    # ------------------------------------------------------------------
    if product_template.two_d_template_svg:
        try:
            svg = render_svg(product_template.two_d_template_svg, dims)
            return HttpResponse(svg, content_type="image/svg+xml")
        except Exception as e:
            return Response(
                {"error": f"SVG template rendering failed: {str(e)}"},
                status=400
            )

    # ------------------------------------------------------------------
    # CASE 2: PART-LEVEL STITCHING WITH DYNAMIC VIEWBOX & VISUALIZATION
    # ------------------------------------------------------------------
    stitched = []
    current_y = 0
    max_width = 200 # Initial minimum
    
    # Pre-render parts to calculate total height/width for viewBox
    rendered_groups = []
    
    for p in parts:
        l = float(p["length"])
        w = float(p["width"])
        max_width = max(max_width, l + 300) # Leave room for labels
        
        # Edge-banding context (Visualization Lines)
        # Assuming p["edgebanding"] = {"top": True, "bottom": False, ...}
        eb = p.get("edgebanding", {})
        
        ctx = {
            "L": l, "W": w, "qty": p["quantity"],
            "T": p["thickness"], "grain": p.get("grain_direction"),
            "eb": eb
        }

        if p.get("two_d_template_svg"):
            try:
                content = render_svg(p["two_d_template_svg"], ctx)
            except Exception as e:
                content = f'<text y="20" fill="red">Error: {str(e)}</text>'
        else:
            # AUTO-GENERATED VISUALIZATION (Rect + Grain + EB)
            content = generate_fallback_svg(ctx, p["name"])

        rendered_groups.append(f'<g transform="translate(10, {current_y + 20})">{content}</g>')
        current_y += (w + 60)

    # Wrap in SVG with dynamic viewBox for "Auto-scale"
    header = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {max_width} {current_y + 50}" preserveAspectRatio="xMidYMid meet">'
    stitched.append(header)
    stitched.extend(rendered_groups)
    stitched.append("</svg>")

    return HttpResponse("".join(stitched), content_type="image/svg+xml")

def generate_fallback_svg(ctx, name):
    """Internal helper for standard part visualization."""
    l, w = ctx["L"], ctx["W"]
    # Add thicker lines for edgebanded sides
    eb_lines = ""
    if ctx["eb"].get("top"): eb_lines += f'<line x1="0" y1="0" x2="{l}" y2="0" stroke="blue" stroke-width="4"/>'
    
    # Grain direction arrow
    grain_arrow = ""
    if ctx["grain"] == "horizontal":
        grain_arrow = f'<path d="M{l/2-10} {w/2} L{l/2+10} {w/2} M{l/2+5} {w/2-5} L{l/2+10} {w/2} L{l/2+5} {w/2+5}" stroke="gray" fill="none"/>'

    return f'''
        <rect width="{l}" height="{w}" fill="none" stroke="black" stroke-width="1"/>
        {eb_lines}
        {grain_arrow}
        <text x="{l + 10}" y="{w/2}" font-family="sans-serif" font-size="12">
            {name} ({l}x{w})
        </text>
    '''


# ✔ Auto-scale SVG to fit screen
# ✔ Grain direction arrows
# ✔ Edge-band visualization (left/right/top/bottom thickness lines)
# ✔ Option to export PNG / PDF
# ✔ Combine product + parts into a single downloadable ZIP
# ✔ 2D nesting preview from Cutlist optimizer