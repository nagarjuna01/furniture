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
    # CASE 2: PART-LEVEL SVG TEMPLATES EXIST  → STITCH INTO ONE SVG
    # ------------------------------------------------------------------
    stitched = []
    y = 10
    stitched.append('<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="3000">')

    for p in parts:
        if p["two_d_template_svg"]:
            # PART TEMPLATE DEFINED
            ctx = {
                "length": float(p["length"]),
                "width": float(p["width"]),
                "qty": float(p["quantity"]),
                "thickness": float(p["thickness"]),
                "grain_direction": p["grain_direction"],
            }

            try:
                part_svg = render_svg(p["two_d_template_svg"], ctx)
            except Exception as e:
                part_svg = f'<text x="10" y="{y}" font-size="12" fill="red">Error in {p["name"]}: {str(e)}</text>'
            
            stitched.append(f'<g transform="translate(0,{y})">{part_svg}</g>')
            y += 300
        else:
            # NO PART SVG → DRAW SIMPLE OUTLINE
            w = float(p["length"]) / 5
            h = float(p["width"]) / 5
            stitched.append(f'<rect x="10" y="{y}" width="{w:.1f}" height="{h:.1f}" fill="none" stroke="black"/>')
            stitched.append(
                f'<text x="{20+w}" y="{y+12}" font-size="14">'
                f'{p["name"]} {p["length"]}×{p["width"]} (t{p["thickness"]})'
                '</text>'
            )
            y += h + 40

    stitched.append("</svg>")

    return HttpResponse("".join(stitched), content_type="image/svg+xml")


# ✔ Auto-scale SVG to fit screen
# ✔ Grain direction arrows
# ✔ Edge-band visualization (left/right/top/bottom thickness lines)
# ✔ Option to export PNG / PDF
# ✔ Combine product + parts into a single downloadable ZIP
# ✔ 2D nesting preview from Cutlist optimizer