# material/views.py

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets
from .models import Brand, Category, CategoryTypes, CategoryModel, WoodEn, EdgeBand, HardwareGroup, Hardware,EdgebandName
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
    HardwareGroupSerializer, HardwareSerializer, EdgebandNameSerializer # Unified serializer
)

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
    return render(request, 'ctmwmo.html')

def hardware_view(request):
    return render(request, 'hardware_list.html')  # Update template name if needed

def edgeband_list(request):
    return render(request, 'edgeband_list_copy.html')

def category_browser(request):
    return render(request, 'categorybrowser_copy.html')

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

class EdgebandNameViewSet(viewsets.ModelViewSet):
    queryset = EdgebandName.objects.all().order_by("name")
    serializer_class = EdgebandNameSerializer

class EdgeBandViewSet(viewsets.ModelViewSet):
    queryset = EdgeBand.objects.all().order_by("-id")
    serializer_class = EdgeBandSerializer # Use the unified EdgeBandSerializer
    # pagination_class = CustomPagination # Removed as requested


# --------------------- WOODEN ---------------------
class WoodEnViewSet(viewsets.ModelViewSet):
    queryset = WoodEn.objects.all()
    serializer_class = WoodEnSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    
    # allow exact filters
    filterset_fields = ['material_grp', 'brand', 'thickness', 'material_type', 'material_model']
    
    # allow text search
    search_fields = ['name', 'thickness']

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        # ✅ optional extra manual filtering
        name = params.get("name")
        if name:
            queryset = queryset.filter(name__icontains=name)

        category = params.get("category")   # assuming mapped to material_grp
        if category:
            queryset = queryset.filter(material_grp=category)

        type_id = params.get("type")        # assuming mapped to material_type
        if type_id:
            queryset = queryset.filter(material_type=type_id)

        model_id = params.get("model")      # mapped to material_model
        if model_id:
            queryset = queryset.filter(material_model_id=model_id)

        brand_id = params.get("brand")
        if brand_id:
            queryset = queryset.filter(brand=brand_id)

        return queryset

    

# --------------------- HARDWARE ---------------------
class HardwareGroupViewSet(viewsets.ModelViewSet):
    queryset = HardwareGroup.objects.all()
    serializer_class = HardwareGroupSerializer

class HardwareViewSet(viewsets.ModelViewSet):
    queryset = Hardware.objects.all()
    serializer_class = HardwareSerializer # Use the unified HardwareSerializer
    # pagination_class = CustomPagination # Removed as requested
