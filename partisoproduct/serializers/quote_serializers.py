from rest_framework import serializers
from partisoproduct.models import QuoteRequest, QuotePartDetail, QuoteProduct, Part1
from material.models.wood import WoodMaterial
from material.models.edgeband import EdgeBand
from material.models.hardware import Hardware

# -- Nested Serializers for Detailed Output (Read) --

class QuotePartDetailSerializer(serializers.ModelSerializer):
    part_name = serializers.CharField(source='part_template.name', read_only=True)
    selected_material_name = serializers.CharField(source='selected_material.name', read_only=True)

    class Meta:
        model = QuotePartDetail
        fields = [
            'part_template', 'selected_material', 'part_name', 'selected_material_name',
            'evaluated_dimensions', 'evaluated_qty', 'evaluated_area',
            'wastage_multiplier', 'material_cost', 'edge_cost',
            'hardware_cost', 'total_cost'
        ]
        read_only_fields = [
            'evaluated_dimensions', 'evaluated_qty', 'evaluated_area',
            'wastage_multiplier', 'material_cost', 'edge_cost',
            'hardware_cost', 'total_cost'
        ]

class QuoteProductDetailSerializer(serializers.ModelSerializer):
    part_details = QuotePartDetailSerializer(many=True, read_only=True)
    modular_product_name = serializers.CharField(source='modular_product.name', read_only=True)
    
    class Meta:
        model = QuoteProduct
        fields = [
            'id', 'modular_product', 'modular_product_name', 'length_mm', 'width_mm',
            'height_mm', 'quantity', 'total_product_cost', 'part_details'
        ]

# -- Serializer for Nested Input (Write) --

class QuoteProductWriteSerializer(serializers.ModelSerializer):
    part_details = QuotePartDetailSerializer(many=True, required=False)

    class Meta:
        model = QuoteProduct
        fields = [
            'modular_product', 'length_mm', 'width_mm', 'height_mm', 'quantity', 'part_details'
        ]

# -- The Hybrid Serializer --

class HybridQuoteRequestSerializer(serializers.ModelSerializer):
    products = QuoteProductDetailSerializer(many=True, read_only=True)

    class Meta:
        model = QuoteRequest
        fields = ['id', 'customer_name', 'created_at', 'products']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if 'view' in self.context and self.context['view'].action in ['create', 'calculate_quote']:
            self.fields['products'] = QuoteProductWriteSerializer(many=True, required=True)

    def create(self, validated_data):
        products_data = validated_data.pop('products')
        
        quote_request = QuoteRequest.objects.create(**validated_data)
        
        for product_data in products_data:
            part_details_data = product_data.pop('part_details', [])
            quote_product = QuoteProduct.objects.create(quote=quote_request, **product_data)
            
            for part_detail_data in part_details_data:
                part_template = part_detail_data.get('part_template')
                
                # You need to implement your calculation logic here.
                # For example, by calling a service or function.
                calculated_data = {
                    'evaluated_qty': 1, # Placeholder
                    'evaluated_area': 0.0, # Placeholder
                    'material_cost': 0.0, # Placeholder
                    'total_cost': 0.0, # Placeholder
                    'part_name': part_template.name if part_template else None,
                }
                
                QuotePartDetail.objects.create(
                    quote_product=quote_product,
                    **part_detail_data,
                    **calculated_data
                )
        return quote_request