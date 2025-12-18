from rest_framework import serializers
from decimal import Decimal

class PartCutSerializer(serializers.Serializer):
    name = serializers.CharField()
    width = serializers.DecimalField(max_digits=8, decimal_places=2)
    height = serializers.DecimalField(max_digits=8, decimal_places=2)
    grain = serializers.CharField()
    x = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)
    y = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)

class SheetSerializer(serializers.Serializer):
    sheet_index = serializers.IntegerField()
    width = serializers.DecimalField(max_digits=8, decimal_places=2)
    height = serializers.DecimalField(max_digits=8, decimal_places=2)
    used_area = serializers.DecimalField(max_digits=10, decimal_places=2)
    remaining_area = serializers.DecimalField(max_digits=10, decimal_places=2)
    waste_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    cuts = PartCutSerializer(many=True)

class CutlistSerializer(serializers.Serializer):
    sheets = SheetSerializer(many=True)
    total_sheets = serializers.IntegerField()
    total_waste_percent = serializers.DecimalField(max_digits=5, decimal_places=2)

class ProductQuoteSummarySerializer(serializers.Serializer):
    total_part_cp = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_part_sp = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_hardware_cp = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_hardware_sp = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_cp = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_sp = serializers.DecimalField(max_digits=10, decimal_places=2)
    required_minimum_sell_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    max_discount_possible = serializers.DecimalField(max_digits=10, decimal_places=2)
    profit_margin = serializers.DecimalField(max_digits=10, decimal_places=2)
    can_offer_discount = serializers.BooleanField()
    discount_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)

class ProductQuoteSerializer(serializers.Serializer):
    bom = serializers.DictField()  # Raw BOM dictionary
    summary = ProductQuoteSummarySerializer()
    # Cutlist is embedded in BOM

class ProductEvaluationSerializer(serializers.Serializer):
    product = serializers.CharField()
    quotes = serializers.DictField(
        child=ProductQuoteSerializer()
    )
