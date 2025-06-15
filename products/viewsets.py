# products/viewsets.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from decimal import Decimal # Needed for calculations

from .models import (
    ProductCategory, Type, Model, Unit, Coupon, Review,
    Part, Module, Product, StandardProduct, CustomProduct,
    ModularProduct, StandardProductImage
)
from .serializers import (
    ProductCategorySerializer, TypeSerializer, ModelSerializer, UnitSerializer,
    CouponSerializer, ReviewSerializer, PartSerializer, ModuleSerializer,
    ProductSerializer, StandardProductSerializer, CustomProductSerializer,
    ModularProductSerializer, StandardProductImageSerializer,ModuleDetailSerializer
)

# --- Basic Classification & Units ViewSets ---
class ProductCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer

class TypeViewSet(viewsets.ModelViewSet):
    queryset = Type.objects.all()
    serializer_class = TypeSerializer

class ModelViewSet(viewsets.ModelViewSet):
    queryset = Model.objects.all()
    serializer_class = ModelSerializer

class UnitViewSet(viewsets.ModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer

class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

# --- Part & Module ViewSets ---
class PartViewSet(viewsets.ModelViewSet):
    queryset = Part.objects.all()
    serializer_class = PartSerializer

class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleDetailSerializer

# --- Product Subclass ViewSets ---
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class StandardProductViewSet(viewsets.ModelViewSet):
    queryset = StandardProduct.objects.all()
    serializer_class = StandardProductSerializer

class StandardProductImageViewSet(viewsets.ModelViewSet):
    queryset = StandardProductImage.objects.all()
    serializer_class = StandardProductImageSerializer

class CustomProductViewSet(viewsets.ModelViewSet):
    queryset = CustomProduct.objects.all()
    serializer_class = CustomProductSerializer

# --- Modular Product ViewSet (Handles main product and its nested components) ---
class ModularProductViewSet(viewsets.ModelViewSet):
    queryset = ModularProduct.objects.all()
    serializer_class = ModularProductSerializer

    # Custom action for calculating live cost
    @action(detail=True, methods=['post'])
    def calculate_live_cost(self, request, pk=None):
        """
        Calculates the live cost of a modular product based on provided constraints.
        This uses the calculate_modular_product_cost method on the ModularProduct model.
        """
        modular_product = self.get_object() # Get the specific ModularProduct instance
        constraints_data = request.data.get('constraints', [])

        # Convert the incoming constraint data into a format suitable for the model's calculation method
        live_local_vars = {}
        for constraint in constraints_data:
            abbr = constraint.get('abbreviation')
            value = constraint.get('value')
            if abbr and value is not None:
                try:
                    live_local_vars[abbr] = Decimal(str(value)) # Convert to string then Decimal for precision
                except (ValueError, TypeError):
                    return Response({'detail': f'Invalid value for constraint {abbr}: {value}'}, status=400)


        # Call the method on the model instance (assuming it exists and returns a dict)
        try:
            calculation_result = modular_product.calculate_modular_product_cost(live_local_vars)
        except Exception as e:
            return Response({'detail': f'Calculation error: {str(e)}'}, status=400)

        # Return a response with the calculated values
        return Response({
            'calculated_purchase_cost': calculation_result.get('total_purchase_cost'),
            'calculated_selling_price': calculation_result.get('total_selling_cost_derived'),
            'break_even_amount': calculation_result.get('break_even_amount'),
            'profit_margin_percentage': calculation_result.get('profit_margin_percentage'),
            # Include any other relevant calculation results
        })
    
# --- New ViewSets for Layout/Rooms (Commented for future use) ---
# class BuildingViewSet(viewsets.ModelViewSet):
#     queryset = Building.objects.all().order_by('name')
#     serializer_class = BuildingSerializer
#     # permission_classes = [IsAuthenticated] # Or more specific permissions
#
#     # Optional: Custom action to trigger 3D model regeneration for a building
#     # @action(detail=True, methods=['post'], url_path='generate-3d-model')
#     # def generate_3d_model(self, request, pk=None):
#     #     building = self.get_object()
#     #     # building._generate_3d_model() # Trigger the async task
#     #     return Response({'status': '3D model generation initiated'}, status=status.HTTP_202_ACCEPTED)
#
# class FloorViewSet(viewsets.ModelViewSet):
#     queryset = Floor.objects.all().order_by('building', 'floor_number')
#     serializer_class = FloorSerializer
#     # permission_classes = [IsAuthenticated]
#
#     # Optional: Filter by building
#     # def get_queryset(self):
#     #     queryset = super().get_queryset()
#     #     building_id = self.request.query_params.get('building_id')
#     #     if building_id:
#     #         queryset = queryset.filter(building_id=building_id)
#     #     return queryset
#
# class RoomViewSet(viewsets.ModelViewSet):
#     queryset = Room.objects.all().order_by('floor', 'name')
#     serializer_class = RoomSerializer
#     # permission_classes = [IsAuthenticated]
#
#     # Optional: Custom action to get a specific room's generated 3D model
#     # @action(detail=True, methods=['get'], url_path='3d-model-url')
#     # def get_room_3d_model_url(self, request, pk=None):
#     #     room = self.get_object()
#     #     if room.associated_modular_product and room.associated_modular_product.get_assembled_3d_model_url:
#     #         return Response({'url': room.associated_modular_product.get_assembled_3d_model_url})
#     #     return Response({'detail': '3D model not available for this room'}, status=status.HTTP_404_NOT_FOUND)