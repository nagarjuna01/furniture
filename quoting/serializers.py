from rest_framework import serializers
from decimal import Decimal
from .models import QuoteRequest, QuoteProduct, QuotePart, QuotePartHardware
from material.models.wood import WoodMaterial
from material.models.edgeband import EdgeBand
from material.models.hardware import Hardware
from modular_calc.evaluation.part_evaluator import PartEvaluator  # new engine

# -----------------------------
# HARDWARE
# -----------------------------
class QuotePartHardwareSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    hardware_name = serializers.CharField(source="hardware.name", read_only=True)
    cp = serializers.DecimalField(source="hardware.cp", max_digits=10, decimal_places=2, read_only=True)
    sp = serializers.DecimalField(source="hardware.sp", max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = QuotePartHardware
        fields = ["id","tenant", "hardware", "hardware_name", "quantity", "cp", "sp"]


# -----------------------------
# PARTS
# -----------------------------
class QuotePartSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    hardware = QuotePartHardwareSerializer(many=True, read_only=True)
    material_name = serializers.CharField(source="material.name", read_only=True)
    material_cp = serializers.DecimalField(source="material.cp", max_digits=10, decimal_places=2, read_only=True)
    material_sp = serializers.DecimalField(source="material.sp", max_digits=10, decimal_places=2, read_only=True)
    edgebands = serializers.SerializerMethodField()
    three_d_asset = serializers.SerializerMethodField()
    two_d_template_svg = serializers.SerializerMethodField()

    class Meta:
        model = QuotePart
        fields = [
            "id", "tenant",
            "quote_product",
            "part_template",
            "part_name",
            "length_mm",
            "width_mm",
            "part_qty",
            "thickness_mm",
            "material",
            "material_name",
            "material_cp",
            "material_sp",
            "edgebands",
            "shape_wastage_multiplier",
            "area_mm2",
            "area_sqft",
            "three_d_asset",
            "two_d_template_svg",
            "cutting_charges",
            "making_charges",
            "total_cost",
            "override_by_employee",
            "override_reason",
            "hardware",
        ]
        read_only_fields = ['id','tenant',
            "area_mm2", "area_sqft", "three_d_asset", "two_d_template_svg",
            "cutting_charges", "making_charges", "total_cost"
        ]

    def get_edgebands(self, obj):
        return {
            "top": obj.edgeband_top.name if obj.edgeband_top else None,
            "bottom": obj.edgeband_bottom.name if obj.edgeband_bottom else None,
            "left": obj.edgeband_left.name if obj.edgeband_left else None,
            "right": obj.edgeband_right.name if obj.edgeband_right else None,
        }

    def get_three_d_asset(self, obj):
        try:
            return obj.part_template.three_d_asset.url
        except:
            return None

    def get_two_d_template_svg(self, obj):
        pt = obj.part_template
        if pt.two_d_template_svg:
            return pt.two_d_template_svg
        return getattr(pt.product_template, "two_d_template_svg", None)


# -----------------------------
# PRODUCT UNDER QUOTE
# -----------------------------
class QuoteProductSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    parts = QuotePartSerializer(many=True, read_only=True)
    description = serializers.SerializerMethodField()
    product_name = serializers.CharField(source="product_template.name", read_only=True)

    class Meta:
        model = QuoteProduct
        fields = [
            "id","tenant",
            "quote",
            "product_template",
            "product_name",
            "length_mm",
            "width_mm",
            "height_mm",
            "quantity",
            "validated",
            "description",
            "parts",
        ]
        read_only_fields = ["id","tenant","validated", "description", "parts"]

    def get_description(self, obj):
        return obj.description

    def validate(self, attrs):
        """
        Validate inputs using new PartEvaluator engine.
        """
        product_dims = {
            "product_length": attrs.get("length_mm"),
            "product_width": attrs.get("width_mm"),
            "product_height": attrs.get("height_mm"),
        }
        # Use PartEvaluator to check each part (soft validation)
        for pt in attrs["product_template"].part_templates.all():
            evaluator = PartEvaluator(pt, product_dims, parameters={})
            result = evaluator.evaluate()
            if result["length"] <= 0 or result["width"] <= 0 or result["quantity"] <= 0:
                raise serializers.ValidationError(
                    f"Part {pt.name} evaluated to invalid dimensions or quantity."
                )
        return attrs


# -----------------------------
# QUOTE REQUEST
# -----------------------------
class QuoteRequestSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    products = QuoteProductSerializer(many=True, read_only=True)

    class Meta:
        model = QuoteRequest
        fields = ["id","tenant", "customer_name", "created_by", "created_at", "products"]
        read_only_fields = ["tenant","created_by", "created_at", "products"]


class MarketplaceQuoteSerializer(serializers.ModelSerializer):
    """
    Used for Public Leads / Login Users.
    Calculates dynamic SP but hides all factory/tenant costs.
    """
    calculated_sp = serializers.SerializerMethodField()
    
    class Meta:
        model = QuoteProduct
        fields = [
            'id', 'product_template', 'length_mm', 'width_mm', 
            'height_mm', 'quantity', 'override_material', 'calculated_sp'
        ]

    def get_calculated_sp(self, obj):
        # We only run the engine and extract the final Selling Price
        # No parts list, no edgebands, no internal formulas are returned.
        result = obj.evaluate_now()
        return result.get("total_price")

class TenantQuoteSerializer(serializers.ModelSerializer):
    """
    Used for Workers/Admins.
    Includes full expansion data, hardware details, and Cost Price (CP).
    """
    parts = QuotePartSerializer(many=True, read_only=True) # Full cut-list
    profit_margin = serializers.ReadOnlyField(source='get_margin') # (SP - CP)

    class Meta:
        model = QuoteProduct
        fields = [
            'id', 'quote', 'product_template', 'length_mm', 'width_mm', 
            'height_mm', 'quantity', 'total_sp', 'total_cp', 
            'profit_margin', 'validated', 'config_parameters', 'parts'
        ]