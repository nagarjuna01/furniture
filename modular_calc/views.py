# modular_config/views.py

from rest_framework import viewsets, mixins, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import DecimalField
from django.db.models.functions import Cast
from rest_framework.filters import OrderingFilter  # <-- NEW
from django_filters.rest_framework import DjangoFilterBackend # <-- NEW
from django.db.models import F # <-- NEW IMPORT
from django.shortcuts import render
from .serializers import (
    ModularProductSerializer, 
    WoodEnMiniSerializer, HardwareMiniSerializer,
    EdgeBandMiniSerializer # Assuming you renamed the read-only ones to Mini
)
from .models import ModularProduct
from material.models import WoodEn, EdgeBand,Hardware


# ==============================================================================
#                      1. CORE MODULAR PRODUCT VIEWSET (HYBRID/NESTED)
# ==============================================================================

class ModularProductViewSet(viewsets.ModelViewSet):
    """
    Handles single API call for CRUD of ModularProduct and all nested components.
    Uses ModularProductSerializer for both read and write operations.
    """
    # Use select_related/prefetch_related for better performance on large GET requests
    queryset = ModularProduct.objects.all().prefetch_related(
        'parameters', 
        'hardware_rules', 
        'part_templates__material_whitelist', 
        'part_templates__edgeband_whitelist',
        'part_templates__hardware_rules'
    )
    serializer_class = ModularProductSerializer


# ==============================================================================
#                      2. MATERIAL VIEWSETS FOR FRONTEND DROPDOWNS
# ==============================================================================
# modular_calc/views.py

class WoodEnFilterViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Provides all WoodEn materials, filtered by thickness, and unique thicknesses."""
    
    # 🎯 1. Set the final, ordered queryset as a class attribute
    # This ordering handles the hierarchy: material_grp (Category) -> material_type (Type) -> material_model (Model)
    queryset = WoodEn.objects.all().order_by(
        'material_grp__name', 
        'material_type__name', 
        'material_model__name'
    )
    
    serializer_class = WoodEnMiniSerializer 
    
    # 🎯 2. Define filter backends
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    
    # 🎯 3. Define fields available for filtering via query parameters
    filterset_fields = [
        'thickness', 
        'material_grp__name',
        'material_type__name',
        'material_model__name',
    ]

    # Optional: If you want to allow dynamic ordering via 'ordering' query param:
    ordering_fields = ['thickness', 'material_grp__name', 'material_type__name', 'material_model__name']
    
    @action(detail=False, methods=['get'], url_path='unique_thicknesses')
    def unique_thicknesses(self, request):
        """Returns a list of all unique thicknesses (Decimals) from WoodEn model."""
        # This method is correct and relies only on WoodEn model fields, not filters
        thicknesses = WoodEn.objects.values_list('thickness', flat=True).annotate(
            thickness_decimal=Cast('thickness', output_field=DecimalField())
        ).order_by('thickness_decimal').distinct()
        
        return Response([float(t) for t in thicknesses])


class EdgeBandFilterViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    # Set the default hierarchical ordering
    # We order by brand name and then the nested edgeband name
    queryset = EdgeBand.objects.all().order_by('brand__name', 'edgeband_name__name')
    serializer_class = EdgeBandMiniSerializer
    
    # Enable explicit ordering via query parameters
    filter_backends = [OrderingFilter]
    ordering_fields = ['e_thickness', 'brand__name', 'edgeband_name__name']
    ordering = ['brand__name', 'edgeband_name__name'] # Default ordering

    def get_queryset(self):
        """
        Filters edgebands based on max_thickness_mm query parameter (derived from material thickness).
        The range is: e_thickness must be between [material_thickness + 0] and [material_thickness + 5].
        """
        queryset = self.queryset
        
        # max_thickness is the thickness of the material part (e.g., 18mm)
        material_thickness_str = self.request.query_params.get('material_thickness_mm') 

        if material_thickness_str:
            try:
                material_thickness = float(material_thickness_str)
                
                min_t = material_thickness + 0  
                max_t = material_thickness + 5  
                
                # Filter for edgebands where e_thickness is within the calculated range
                queryset = queryset.filter(e_thickness__gte=min_t, e_thickness__lte=max_t) 
                
            except ValueError:
                # If material_thickness_str is not a valid number, ignore the filter
                pass
        
        return queryset

class HardwareFilterViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    
    # 🎯 1. Set the default hierarchical ordering 
    # Order: Hardware Group -> Brand -> Hardware Name
    queryset = Hardware.objects.all().order_by(
        'h_group__name',      # Category
        'brand__name',        # Brand
        'h_name'              # Item Name
    )
    serializer_class = HardwareMiniSerializer 
    
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    
    # 🎯 2. Define fields available for filtering
    filterset_fields = [
        # Allows filtering by the name of the related objects
        'h_group__name',     
        'brand__name',        
        'unit',
        # You could add filtering by price ranges here if needed
    ]
    
    # Optional: Set the explicit fields that can be ordered by query param
    ordering_fields = ['h_group__name', 'brand__name', 'h_name', 'p_price', 's_price', 'sl_price']
# ==============================================================================
#                      3. UI UTILITY VIEWS
# ==============================================================================
    
def modular_config_ui(request):
    """View for serving the main UI template that uses the nested API."""
    # Assuming you have a template named 'modular_config_ui.html' for your single architecture
    return render(request, 'modular_config_ui.html')

