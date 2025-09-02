from rest_framework import serializers
from .models import (
    ModularProduct, PartTemplate,
    PartMaterialWhitelist, PartEdgeBandWhitelist,
    PartHardwareRule
)
from material.models import EdgeBand

class PartMaterialWhitelistSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartMaterialWhitelist
        fields = ["id", "material", "is_default"]


class PartEdgeBandWhitelistSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartEdgeBandWhitelist
        fields = ["id", "edgeband", "is_default"]


class PartHardwareRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartHardwareRule
        fields = ["id", "hardware", "quantity_equation"]

class EdgeBandMiniSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(source="__str__", read_only=True)

    class Meta:
        model = EdgeBand
        fields = ["id", "display_name"]

class PartTemplateSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(read_only=True)

    material_whitelist = PartMaterialWhitelistSerializer(many=True, read_only=True)
    edgeband_whitelist = PartEdgeBandWhitelistSerializer(many=True, read_only=True)
    hardware_rules = PartHardwareRuleSerializer(many=True, read_only=True)

    # use PrimaryKeyRelatedField for writes, MiniSerializer for reads
    edgeband_top = serializers.PrimaryKeyRelatedField(
        queryset=EdgeBand.objects.all(), allow_null=True, required=False
    )
    edgeband_bottom = serializers.PrimaryKeyRelatedField(
        queryset=EdgeBand.objects.all(), allow_null=True, required=False
    )
    edgeband_left = serializers.PrimaryKeyRelatedField(
        queryset=EdgeBand.objects.all(), allow_null=True, required=False
    )
    edgeband_right = serializers.PrimaryKeyRelatedField(
        queryset=EdgeBand.objects.all(), allow_null=True, required=False
    )

    # represent as MiniSerializer on output
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["edgeband_top"] = EdgeBandMiniSerializer(instance.edgeband_top).data if instance.edgeband_top else None
        rep["edgeband_bottom"] = EdgeBandMiniSerializer(instance.edgeband_bottom).data if instance.edgeband_bottom else None
        rep["edgeband_left"] = EdgeBandMiniSerializer(instance.edgeband_left).data if instance.edgeband_left else None
        rep["edgeband_right"] = EdgeBandMiniSerializer(instance.edgeband_right).data if instance.edgeband_right else None
        return rep

    class Meta:
        model = PartTemplate
        fields = [
            "id", "product", "name",
            "part_length_equation", "part_width_equation", "part_qty_equation",
            "part_thickness_mm",
            "edgeband_top", "edgeband_bottom", "edgeband_left", "edgeband_right",
            "shape_wastage_multiplier",
            "three_d_asset", "two_d_template_svg",
            "material_whitelist", "edgeband_whitelist", "hardware_rules"
        ]


class ModularProductSerializer(serializers.ModelSerializer):
    part_templates = PartTemplateSerializer(many=True, read_only=True)

    class Meta:
        model = ModularProduct
        fields = [
            "id", "name", "product_validation_expression",
            "three_d_asset", "two_d_template_svg",
            "created_at", "updated_at",
            "part_templates"
        ]
