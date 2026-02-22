from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import QuoteRequest, QuoteProduct


# quoting/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from modular_calc.evaluation.product_engine import ProductEngine # Import your engine
from modular_calc.models import ModularProduct 
from material.models.wood import WoodMaterial
from material.models.edgeband import EdgeBand


# quoting/views.py
class ModularCalculateView(APIView):
    def post(self, request):
        data = request.data
        p_id = data.get('product_id')
        mat_id = data.get('wood_id')
        eb_id = data.get('eb_id')
        try:
            # 1. Strict Lookups
            product = ModularProduct.objects.get(id=p_id)
            material = WoodMaterial.objects.get(id=mat_id)
            edgeband = None
            if eb_id:
                edgeband = EdgeBand.objects.select_related('edgeband_name').get(id=eb_id)
            # 2. Build Parameters Context (Mirroring your 'evaluate' logic)
            # Fetch D1FH, FDF, etc., from the DB
            system_defaults = {
                p.abbreviation: float(p.default_value or 0) 
                for p in product.parameters.all()
            }
            
            # Merge with any user overrides sent in the payload
            raw_params = data.get("parameters") or {}
            user_overrides = {
                str(k): float(v) for k, v in raw_params.items() 
                if isinstance(raw_params, dict)
            }
            
            cleaned_params = {**system_defaults, **user_overrides}

            # 3. Build Dimensions (Strict Decimal/Float casting)
            L = float(data.get('l', 1000))
            W = float(data.get('w', 600))
            H = float(data.get('h', 720))

            engine_payload = {
                "product": product,
                "product_dims": {
                    "L": L, "W": W, "H": H,
                    "product_length": L, "product_width": W, "product_height": H
                },
                "parameters": cleaned_params,  
                "selected_material": material,
                "material_selections": {}, 
                "selected_edgeband": edgeband,
                "quantities": [int(data.get('quantity', 1))]
            }

            # 4. Run Engine
            engine = ProductEngine(engine_payload)
            result = engine.run()

            return Response(result, status=status.HTTP_200_OK)

        except ModularProduct.DoesNotExist:
            return Response({"error": f"Product {p_id} not found"}, status=404)
        except WoodMaterial.DoesNotExist:
                    return Response({"error": f"Material {mat_id} not found"}, status=404)
        except EdgeBand.DoesNotExist:
            return Response({"error": "Edgeband Selection not found"}, status=404)
        except Exception as e:
            # No silent killers
            import traceback
            traceback.print_exc() 
            return Response({"error": f"Engine Error: {str(e)}"}, status=400)

@login_required
def quote_list_view(request):
    return render(request, "quote_list.html")

# @login_required
# def quote_create_view(request):
#     """
#     Renders the 'New Quote' form shell.
#     We don't do POST here. The JS will POST to the API to ensure 
#     the Serializer triggers the Quote Number generation and Tenant checks.
#     """
#     return render(request, "quote_create.html")

# @login_required
def quote_detail_view(request, quote_id):
    """
    The main Workspace. 
    Matches your URL: path("quotes/<uuid:quote_id>/", ...)
    """
    # Security: Ensure Factory A cannot access Factory B's UUID
    quote = get_object_or_404(
        QuoteRequest, 
        id=quote_id, 
        tenant=request.user.tenant
    )
    return render(request, "quote_detail.html", {
        "quote_id": str(quote.id),
        "quote_number": quote.quote_number
    })

# @login_required
# def quote_product_view(request, product_id):
#     """
#     Granular editor for a specific cabinet/product.
#     """
#     qp = get_object_or_404(
#         QuoteProduct, 
#         id=product_id, 
#         tenant=request.user.tenant
#     )
#     return render(request, "quote_product.html", {
#         "product_id": qp.id,
#         "product_name": qp.product_template.name if qp.product_template else "Custom Product"
#     })

# from xhtml2pdf import pisa
# from django.template.loader import get_template
# from django.http import HttpResponse

# def render_to_pdf(template_src, context_dict={}):
#     template = get_template(template_src)
#     html = template.render(context_dict)
#     response = HttpResponse(content_type='application/pdf')
#     # Create PDF
#     pisa_status = pisa.CreatePDF(html, dest=response)
#     if pisa_status.err:
#         return HttpResponse('We had some errors <pre>' + html + '</pre>')
#     return response


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import QuoteRequest

@login_required
def quote_workspace_view(request, quote_id):
    """
    Renders the 'Whiteboard' shell. 
    JS takes the quote_id and initializes the quoteState.
    """
    # Strict Tenant Enforcement
    quote = get_object_or_404(
        QuoteRequest, 
        id=quote_id, 
        tenant=request.user.tenant
    )
    
    return render(request, "quoting/workspace.html", {
        "quote": quote,
        "quote_id": str(quote.id)
    })

@login_required
def quote_list_view(request):
    """
    Renders the Pipeline Dashboard.
    Fetches existing quotes for the tenant to display in the table.
    """
    quotes = QuoteRequest.objects.filter(tenant=request.user.tenant).order_by('-created_at')
    return render(request, "quoting/pipeline.html", {"quotes": quotes})