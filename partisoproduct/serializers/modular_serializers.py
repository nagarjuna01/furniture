from rest_framework import serializers
from partisoproduct.models import Modular1, Constraint, HardwareRule
from .part_serializers import Part1Serializer


class ConstraintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Constraint
        fields = ['id', 'modular_product', 'name', 'abbreviation', 'value']


class HardwareRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = HardwareRule
        fields = ['id', 'name', 'equation', 'is_custom']


class Modular1Serializer(serializers.ModelSerializer):
    product_parameters = ConstraintSerializer(many=True, read_only=True)
    hardware_rules = HardwareRuleSerializer(many=True, read_only=True)
    validation_expression = serializers.CharField(
        source='product_validation_expression',
        allow_blank=True, required=False
    )
    parts = Part1Serializer(many=True, read_only=True)

    class Meta:
        model = Modular1
        fields = [
            'id', 'uuid', 'name', 'product_validation_expression',
            'status', 'created_at', 'updated_at',
            'product_parameters', 'hardware_rules','validation_expression','parts'
        ]
