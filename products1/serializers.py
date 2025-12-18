from rest_framework import serializers
from django.db import transaction
import uuid

from .models import (
    Product,
    ProductType,
    ProductSeries,
    MeasurementUnit,
    BillingUnit,
    ProductVariant,
    ProductImage,
    VariantImage,
    AttributeDefinition,
    VariantAttributeValue,
)

class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = ["id", "name", "slug"]

class ProductSeriesSerializer(serializers.ModelSerializer):
    product_type = ProductTypeSerializer(read_only=True)
    product_type_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductType.objects.all(),
        source="product_type",
        write_only=True
    )

    class Meta:
        model = ProductSeries
        fields = ["id", "name", "code", "product_type", "product_type_id"]

class MeasurementUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementUnit
        fields = ["id", "name", "code"]


class BillingUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingUnit
        fields = ["id", "name", "code"]

class AttributeDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeDefinition
        fields = ["id", "name", "field_type", "choices"]
        extra_kwargs = {"choices": {"required": False}}

class ProductImageSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=True
    )

    class Meta:
        model = ProductImage
        fields = ["id", "product", "image", "is_primary"]

class VariantImageSerializer(serializers.ModelSerializer):
    variant = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(),
        write_only=True
    )

    class Meta:
        model = VariantImage
        fields = ["id", "variant", "image", "is_primary"]

    
class VariantAttributeValueSerializer(serializers.ModelSerializer):
    attribute = AttributeDefinitionSerializer(read_only=True)
    attribute_id = serializers.PrimaryKeyRelatedField(
        queryset=AttributeDefinition.objects.all(),
        source="attribute",
        write_only=True
    )

    class Meta:
        model = VariantAttributeValue
        fields = ["id", "attribute", "attribute_id", "value"]


class ProductSerializer(serializers.ModelSerializer):
    sku = serializers.CharField(read_only=True)

    product_type = ProductTypeSerializer(read_only=True)
    product_type_id = serializers.PrimaryKeyRelatedField(
        source="product_type",
        queryset=ProductType.objects.all(),
        write_only=True,
        required=True
    )

    product_series = ProductSeriesSerializer(read_only=True)
    product_series_id = serializers.PrimaryKeyRelatedField(
        source="product_series",
        queryset=ProductSeries.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )
    
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "sku",
            "product_type",
            "product_type_id",
            "product_series",
            "product_series_id",
            "is_active",
            "created_at",
            "images",
        ]

class ProductVariantSerializer(serializers.ModelSerializer):
    sku = serializers.CharField(read_only=True)

    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source="product",
        write_only=True
    )

    measurement_unit = MeasurementUnitSerializer(read_only=True)
    measurement_unit_id = serializers.PrimaryKeyRelatedField(
        queryset=MeasurementUnit.objects.all(),
        source="measurement_unit",
        write_only=True,
        allow_null=True,
        required=False
    )

    billing_unit = BillingUnitSerializer(read_only=True)
    billing_unit_id = serializers.PrimaryKeyRelatedField(
        queryset=BillingUnit.objects.all(),
        source="billing_unit",
        write_only=True,
        allow_null=True,
        required=False
    )

    attributes = VariantAttributeValueSerializer(many=True, read_only=True)
    images = VariantImageSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "sku",
            "product",
            "product_id",
            "length",
            "width",
            "height",
            "weight",
            "measurement_unit",
            "measurement_unit_id",
            "billing_unit",
            "billing_unit_id",
            "purchase_price",
            "selling_price",
            "attributes",
            "images",
            "is_active",
        ]

    def create(self, validated_data):
        product = validated_data["product"]
        validated_data["sku"] = f"{product.sku}-{uuid.uuid4().hex[:6].upper()}"
        return super().create(validated_data)