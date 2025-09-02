from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse
from quoting.models import QuoteProduct

from .services import render_svg

@api_view(["GET"])
def product_svg(request, quote_product_id: int):
    """
    Renders 2D SVG for a product:
    - Uses product two_d_template_svg if present, else falls back to each part's SVG template stitched (simple).
    Context variables: product_length, product_width, product_height, product_depth
    """
    qp = QuoteProduct.objects.select_related("product_template").get(pk=quote_product_id)
    product = qp.product_template
    ctx = qp.as_dims()

    if product.two_d_template_svg:
        svg = render_svg(product.two_d_template_svg, ctx)
        return HttpResponse(svg, content_type="image/svg+xml")

    # Fallback: simple composite from parts (minimal demo)
    parts = qp.parts.all()
    chunks = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1200">']
    y = 10
    for p in parts:
        # Draw rectangles proportional; you can scale based on real dims
        w = float(p.length_mm) / 5
        h = float(p.width_mm) / 5
        chunks.append(f'<rect x="10" y="{y}" width="{w:.1f}" height="{h:.1f}" fill="none" stroke="black"/>')
        chunks.append(f'<text x="{10+w+5}" y="{y+12}" font-size="12">{p.part_name} {p.length_mm}x{p.width_mm} (t{p.thickness_mm})</text>')
        y += h + 20
    chunks.append("</svg>")
    return HttpResponse("".join(chunks), content_type="image/svg+xml")
