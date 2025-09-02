from rest_framework import serializers
from .models import QuoteRequest, QuoteProduct, QuotePart, QuotePartHardware
from modular_calc.models import ModularProduct, PartTemplate
from material.models import WoodEn, EdgeBand


class QuotePartHardwareSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotePartHardware
        fields = ["id", "hardware", "quantity"]


class QuotePartSerializer(serializers.ModelSerializer):
    hardware = QuotePartHardwareSerializer(many=True, read_only=True)

    class Meta:
        model = QuotePart
        fields = [
            "id", "quote_product", "part_template", "part_name",
            "length_mm", "width_mm", "part_qty", "thickness_mm",
            "material",
            "edgeband_top", "edgeband_bottom", "edgeband_left", "edgeband_right",
            "shape_wastage_multiplier",
            "area_mm2", "area_sqft",
            "cutting_charges", "making_charges", "total_cost",
            "override_by_employee", "override_reason",
            "hardware",
        ]
        read_only_fields = ["area_mm2", "area_sqft", "cutting_charges", "making_charges", "total_cost"]


class QuoteProductSerializer(serializers.ModelSerializer):
    parts = QuotePartSerializer(many=True, read_only=True)
    description = serializers.SerializerMethodField()

    class Meta:
        model = QuoteProduct
        fields = [
            "id", "quote", "product_template",
            "length_mm", "width_mm", "height_mm", "depth_mm", "quantity",
            "validated", "description", "parts",
        ]
        read_only_fields = ["validated", "description", "parts"]

    def get_description(self, obj):
        return obj.description

    def validate(self, attrs):
        # soft validation here; hard validation in action if you prefer
        instance = QuoteProduct(**attrs)
        if not instance.validate_inputs():
            raise serializers.ValidationError("Product dimensions do not satisfy product_validation_expression.")
        return attrs


class QuoteRequestSerializer(serializers.ModelSerializer):
    products = QuoteProductSerializer(many=True, read_only=True)

    class Meta:
        model = QuoteRequest
        fields = ["id", "customer_name", "created_by", "created_at", "products"]
        read_only_fields = ["created_by", "created_at"]
