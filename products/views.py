# products/views.py
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
# Note: ListView and DetailView are less useful here if JS fetches all data.
# We will explicitly render templates.
from .models import ModularProduct # Only if needed for initial context
from .models import ModularProduct, Part, Module # Import Module here
from .serializers import ModularProductSerializer, PartSerializer, ModuleSerializer # Import ModuleSerializer
# --- Basic Frontend Views ---

class HomeView(TemplateView):
    template_name = 'home.html'

def product_list_view(request):
    """
    Serves the product list shell. JavaScript will fetch and render products.
    """
    # We still need categories for the filter dropdown on the initial load.
    from .models import ProductCategory # Import locally to avoid circular
    categories = ProductCategory.objects.all()
    context = {
        'categories': categories,
        'initial_category_id': request.GET.get('category'), # Pass initial filter from URL
        'initial_product_type': request.GET.get('product_type'), # Pass initial type from URL
    }
    return render(request, 'product_list.html', context)

def product_detail_view(request, slug):
    """
    Serves the product detail shell. JavaScript will fetch and render product details.
    """
    # We fetch the product minimally just to get its ID for the JS API call,
    # and to confirm it exists and pass the slug.
    from .models import Product # Import locally
    product = get_object_or_404(Product, slug=slug)
    context = {
        'product_slug': slug,
        'product_pk': product.pk, # Useful for fetching reviews linked to this product
    }
    return render(request, 'product_detail.html', context)


# --- Modular Product Configurator View (AJAX heavy) ---
def modular_product_configurator(request, pk):
    # This view still needs to fetch the ModularProduct to provide initial data
    # for the configurator form and the 3D model path.
    modular_product = get_object_or_404(ModularProduct, pk=pk)
    
    # Initial constraints for the form, passed to JS for rendering the input fields
    # We're passing the actual constraint objects, not just values, so JS can
    # get abbreviation and any min/max/step info if needed (not in current model)
    constraints_data = list(modular_product.constraints.values('abbreviation', 'value'))

    context = {
        'modular_product_pk': modular_product.pk,
        'modular_product_name': modular_product.name,
        'modular_product_description': modular_product.description,
        'threed_model_assembly_file_url': modular_product.threed_model_assembly_file.url if modular_product.threed_model_assembly_file else '',
        'threed_config_json_data': modular_product.threed_config_json,
        'initial_constraints_data': constraints_data, # Pass initial constraint structure
    }
    return render(request, 'modular_product_configurator.html', context)

def modular_product_admin_configurator(request, pk):
    """
    Renders the custom admin page for configuring a specific modular product.
    If pk is 0, it's for creating a new product.
    Requires staff (admin) authentication (when enabled).
    """
    modular_product_id = pk
    modular_product_name = "New Modular Product" # Default for new product

    # Fetch all available Modules and Parts for frontend dropdowns
    all_modules = Module.objects.all()
    all_parts = Part.objects.all() # Needed for ModulePart management if Module is editable in this UI

    # Serialize them minimally for JavaScript consumption
    # Use the same serializers as your API, but ensure they don't pull too much data if not needed
    all_modules_data = ModuleSerializer(all_modules, many=True).data
    all_parts_data = PartSerializer(all_parts, many=True).data

    if pk != 0: # If it's an existing product
        try:
            product = get_object_or_404(ModularProduct, pk=pk)
            modular_product_name = product.name
        except Exception:
            # Handle case where product might not exist
            modular_product_name = "Product Not Found"

    context = {
        'modular_product_id': modular_product_id,
        'modular_product_name': modular_product_name,
        'all_modules_json': all_modules_data, # Pass as JSON string
        'all_parts_json': all_parts_data,     # Pass as JSON string (if needed for nested module management)
        # 'CSRF_TOKEN': request.META.get('CSRF_COOKIE', '') # Keep commented out if no auth
    }
    return render(request, 'modular_product_admin_configurator.html', context)


# @staff_member_required # Keep commented out for now
def modular_product_admin_list(request):
    """
    Renders a list of modular products for the custom admin interface.
    """
    return render(request, 'modular_product_admin_list.html')