# material/views.py

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets
from .models import Brand, Category, CategoryTypes, CategoryModel, WoodEn, EdgeBand, HardwareGroup, Hardware
from django.db import connection
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend

# Import the unified serializers
from .serializers import (
    BrandSerializer,
    EdgeBandSerializer, # Unified serializer
    CategorySerializer, CategoryTypesSerializer, CategoryModelSerializer,
    WoodEnSerializer,   # Unified serializer
    HardwareGroupSerializer, HardwareSerializer # Unified serializer
)
# from .pagination import CustomPagination # Removed CustomPagination import as it's no longer used by these viewsets


# --- HTML Template Views (unchanged from your input) ---

def brand_list_page(request):
    return render(request, 'brand_management.html', {})

def category_list1(request):
    categories = Category.objects.all()
    return render(request, 'category_list1.html', {
        'categories': categories
    })

def category_types(request):
    category_id = request.GET.get('categoryId')  # Get the categoryId from the query parameters
    # Optionally, pass the category_id to the template if needed
    return render(request, 'category_types.html', {'category_id': category_id})

def category_type_list(request, category_id=None):
    if category_id is None:
        # No category_id provided, so show all categories
        categories = Category.objects.all()
        return render(request, 'category_list1.html', {'categories': categories})
    
    # If category_id is provided, fetch the category and its types
    category = get_object_or_404(Category, id=category_id)
    category_types = CategoryTypes.objects.filter(category=category)
    return render(request, 'category_types.html', {'category': category, 'category_types': category_types})

def category_models(request, category_type_id):
    category_type = get_object_or_404(CategoryTypes, id=category_type_id)
    models = CategoryModel.objects.filter(model_category=category_type)

    return render(request, 'category_models.html', {
        'category_type': category_type,
        'models': models,
        'categoryTypeId': category_type_id
    })

def filter_categories_by_select(request):
    select_value = request.GET.get('select')
    if select_value:
        categories = Category.objects.filter(name__icontains=select_value)  # Filter categories based on 'select' value
        category_data = [{'id': category.id, 'name': category.name} for category in categories]
        return JsonResponse(category_data, safe=False)
    return JsonResponse({'error': 'No select parameter provided'}, status=400)

def wooden_products(request):
    return render(request, 'wooden_template_bootstrap.html')

def hardware_view(request):
    return render(request, 'hardware_list.html')  # Update template name if needed

def edgeband_list(request):
    return render(request, 'edgeband_list.html')

def category_browser(request):
    return render(request, 'categorybrowser.html')


# --- REST Framework ViewSets ---

# --------------------- BRAND ---------------------
class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer


# --------------------- CATEGORY STRUCTURE ---------------------
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class CategoryTypesViewSet(viewsets.ModelViewSet):
    queryset = CategoryTypes.objects.all()
    serializer_class = CategoryTypesSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category']

class CategoryModelViewSet(viewsets.ModelViewSet):
    queryset = CategoryModel.objects.all()
    serializer_class = CategoryModelSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['model_category']


# --------------------- EDGEBAND ---------------------
class EdgeBandViewSet(viewsets.ModelViewSet):
    queryset = EdgeBand.objects.all()
    serializer_class = EdgeBandSerializer # Use the unified EdgeBandSerializer
    # pagination_class = CustomPagination # Removed as requested


# --------------------- WOODEN ---------------------
class WoodEnViewSet(viewsets.ModelViewSet):
    queryset = WoodEn.objects.all()
    serializer_class = WoodEnSerializer # Use the unified WoodEnSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['material_grp', 'brand', 'thickness']
    search_fields = ['name', 'thickness']
    
    
    def get_queryset(self):
        model_id = self.request.query_params.get('model')
        if model_id:
            return WoodEn.objects.filter(material_model_id=model_id)
        return WoodEn.objects.all()

    @action(detail=True, methods=['get'], url_path='matching_edgebands')
    def matching_edgebands(self, request, pk=None):
        wood = self.get_object()
        target_thickness_str = str(wood.thickness)
        
        if connection.vendor == 'sqlite':
            all_bands = EdgeBand.objects.filter(brand=wood.brand)
            matches = [
                band for band in all_bands
                if target_thickness_str in (band.compatible_thicknesses or [])
            ]
        else:
            matches = EdgeBand.objects.filter(
                compatible_thicknesses__contains=[target_thickness_str],
                brand=wood.brand
            )
        serializer = EdgeBandSerializer(matches, many=True)
        return Response(serializer.data)

# --------------------- HARDWARE ---------------------
class HardwareGroupViewSet(viewsets.ModelViewSet):
    queryset = HardwareGroup.objects.all()
    serializer_class = HardwareGroupSerializer

class HardwareViewSet(viewsets.ModelViewSet):
    queryset = Hardware.objects.all()
    serializer_class = HardwareSerializer # Use the unified HardwareSerializer
    # pagination_class = CustomPagination # Removed as requested
