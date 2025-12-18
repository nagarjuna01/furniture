# # material/views.py

import logging
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from rest_framework.decorators import action
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend



# logger = logging.getLogger(__name__)
 
# # ---------------------------------------------------------
# # TEMPLATE VIEWS
# # ---------------------------------------------------------

def brand_list_page(request):
    return render(request, "brand_management.html", {})

# # def category_list1(request):
# #     return render(request, "category_list1.html", {
# #         "categories": Category.objects.all()
# #     })

# # def category_types(request):
# #     category_id = request.GET.get("categoryId")
# #     return render(request, "category_types.html", {
# #         "category_id": category_id
# #     })

# # def category_type_list(request, category_id=None):
# #     if not category_id:
# #         return render(request, "category_list1.html", {
# #             "categories": Category.objects.all()
# #         })
# #     category = get_object_or_404(Category, id=category_id)
# #     category_types = CategoryTypes.objects.filter(category=category)

# #     return render(request, "category_types.html", {
# #         "category": category,
# #         "category_types": category_types
# #     })

# # def category_models(request, category_type_id):
# #     category_type = get_object_or_404(CategoryTypes, id=category_type_id)
# #     models = CategoryModel.objects.filter(model_category=category_type)
# #     return render(request, "category_models.html", {
# #         "category_type": category_type,
# #         "models": models,
# #         "categoryTypeId": category_type_id
# #     })

# # def filter_categories_by_select(request):
# #     select_value = request.GET.get("select")
# #     if not select_value:
# #         return JsonResponse({"error": "select parameter missing"}, status=400)

# #     categories = Category.objects.filter(name__icontains=select_value)
# #     return JsonResponse([
# #         {"id": c.id, "name": c.name} for c in categories
# #     ], safe=False)

# # def wooden_products(request):
# #     return render(request, "ctmwmo.html")

def hardware_view(request):
    return render(request, "hardware_list.html")

def edgeband_list(request):
    return render(request, "edgeband_list_copy.html")

def category_browser(request):
    return render(request, "categorybrowser_copy.html")

from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import IntegrityError, transaction
from rest_framework.viewsets import ModelViewSet

from material.models.brand import Brand
from material.models.units import MeasurementUnit, BillingUnit
from material.models.category import Category, CategoryTypes, CategoryModel
from material.models.wood import WoodMaterial
from material.models.edgeband import EdgeBand,EdgebandName
from material.models.hardware import Hardware,HardwareGroup

from material.serializers import (
    BrandSerializer,
    MeasurementUnitSerializer,
    BillingUnitSerializer,
    CategorySerializer,
    CategoryTypesSerializer,
    CategoryModelSerializer,
)


# -------------------------------
# Brand ViewSet
# -------------------------------
class BrandViewSet( viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "id"]

# -------------------------------
# MeasurementUnit ViewSet
# -------------------------------
class MeasurementUnitViewSet( viewsets.ModelViewSet):
    queryset = MeasurementUnit.objects.all()
    serializer_class = MeasurementUnitSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code"]


# -------------------------------
# BillingUnit ViewSet
# -------------------------------
class BillingUnitViewSet(ModelViewSet):
    queryset = BillingUnit.objects.all()
    serializer_class = BillingUnitSerializer
    permission_classes = [IsAuthenticated]


# -------------------------------
# Category ViewSets
# -------------------------------
class CategoryViewSet( viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]


class CategoryTypesViewSet(ModelViewSet):
    queryset = CategoryTypes.objects.all()
    serializer_class = CategoryTypesSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]


class CategoryModelViewSet(ModelViewSet):
    queryset = CategoryModel.objects.all()
    serializer_class = CategoryModelSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]


# -------------------------------
# WoodMaterial, EdgeBand, Hardware ViewSets
# -------------------------------
from material.serializers import (
    WoodMaterialSerializer,
    EdgeBandSerializer,
    HardwareSerializer,
    EdgebandNameSerializer,
    HardwareGroupSerializer
)

class WoodMaterialViewSet( viewsets.ModelViewSet):
    queryset = WoodMaterial.objects.all()
    serializer_class = WoodMaterialSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "cost_price", "sell_price"]


class EdgebandNameViewSet( viewsets.ModelViewSet):
    queryset = EdgebandName.objects.all()
    serializer_class = EdgebandNameSerializer
    permission_classes =[IsAuthenticated]

class EdgeBandViewSet( viewsets.ModelViewSet):
    queryset = EdgeBand.objects.all()
    serializer_class = EdgeBandSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["edgeband_name__name", "brand__name"]
    ordering_fields = ["edgeband_name", "brand", "cost_price"]

    

class HardwareGroupViewSet(ModelViewSet):
    queryset = HardwareGroup.objects.all()
    serializer_class = HardwareGroupSerializer
    permission_classes =[IsAuthenticated]
    
class HardwareViewSet( viewsets.ModelViewSet):
    queryset = Hardware.objects.all()
    serializer_class = HardwareSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["h_name", "brand__name"]
    ordering_fields = ["h_name", "brand", "p_price", "s_price"]
    