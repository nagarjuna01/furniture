from rest_framework import serializers
from decimal import Decimal


# -----------------------------
# Cutlist Serializers
# -----------------------------

class PartCutSerializer(serializers.Serializer):
    part_name = serializers.CharField()
    length = serializers.DecimalField(max_digits=8, decimal_places=2)
    width = serializers.DecimalField(max_digits=8, decimal_places=2)

    quantity = serializers.IntegerField()
    grain = serializers.CharField(required=False, allow_blank=True)

    # Placement (for visualizer)
    x = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)
    y = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)

    thickness = serializers.DecimalField(
        max_digits=6, decimal_places=2, required=False
    )


class SheetSerializer(serializers.Serializer):
    sheet_index = serializers.IntegerField()

    sheet_length = serializers.DecimalField(max_digits=8, decimal_places=2)
    sheet_width = serializers.DecimalField(max_digits=8, decimal_places=2)

    used_area = serializers.DecimalField(max_digits=10, decimal_places=2)
    remaining_area = serializers.DecimalField(max_digits=10, decimal_places=2)
    waste_percent = serializers.DecimalField(max_digits=5, decimal_places=2)

    cuts = PartCutSerializer(many=True)


class CutlistSerializer(serializers.Serializer):
    sheets = SheetSerializer(many=True)

    total_sheets = serializers.IntegerField()
    total_used_area = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False
    )
    total_waste_percent = serializers.DecimalField(
        max_digits=5, decimal_places=2
    )


# -----------------------------
# Pricing / Quote Serializers
# -----------------------------

class ProductQuoteSummarySerializer(serializers.Serializer):
    # Cost Price (Sheet + Hardware)
    total_part_cp = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_hardware_cp = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_cp = serializers.DecimalField(max_digits=12, decimal_places=2)

    # Selling Price (Area-based)
    total_part_sp = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_hardware_sp = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_sp = serializers.DecimalField(max_digits=12, decimal_places=2)

    # Discount Safety
    required_minimum_sell_price = serializers.DecimalField(
        max_digits=12, decimal_places=2
    )
    max_discount_possible = serializers.DecimalField(
        max_digits=5, decimal_places=2
    )
    discount_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2
    )

    profit_margin = serializers.DecimalField(
        max_digits=5, decimal_places=2
    )

    can_offer_discount = serializers.BooleanField()


class ProductQuoteSerializer(serializers.Serializer):
    bom = serializers.DictField()
    cutlist = CutlistSerializer()
    summary = ProductQuoteSummarySerializer()


class ProductEvaluationSerializer(serializers.Serializer):
    product = serializers.CharField()

    # Key = pricing mode / tenant / scenario
    quotes = serializers.DictField(
        child=ProductQuoteSerializer()
    )
