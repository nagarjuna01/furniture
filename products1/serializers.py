from rest_framework import serializers
import uuid

from .models import (
    Product,
    ProductType,
    ProductSeries,
    ProductVariant,
    ProductImage,
    VariantImage,
    AttributeDefinition,
    VariantAttributeValue,
    ProductBundle,ProductTemplate,
)
from material.models import MeasurementUnit, BillingUnit


# -------------------------
# PRODUCT TYPE / SERIES
# -------------------------

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


# -------------------------
# ATTRIBUTE SERIALIZERS
# -------------------------

class AttributeDefinitionSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = AttributeDefinition
        fields = ["id", "tenant", "name", "field_type", "choices"]


class VariantAttributeInlineSerializer(serializers.ModelSerializer):
    attribute = AttributeDefinitionSerializer(read_only=True)

    class Meta:
        model = VariantAttributeValue
        fields = ["id", "attribute", "value"]


class VariantAttributeValueSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)

    attribute_id = serializers.PrimaryKeyRelatedField(
        queryset=AttributeDefinition.objects.all(),
        source="attribute",
        write_only=True
    )

    class Meta:
        model = VariantAttributeValue
        fields = ["id", "tenant", "attribute_id", "value"]


# -------------------------
# VARIANT IMAGE SERIALIZERS
# -------------------------

class VariantImageInlineSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = VariantImage
        fields = ["id", "image_url", "is_primary"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url


class VariantImageSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)

    variant_id = serializers.PrimaryKeyRelatedField(
        source="variant",
        queryset=ProductVariant.objects.all(),
        write_only=True
    )

    image_url = serializers.SerializerMethodField()

    class Meta:
        model = VariantImage
        fields = ["id", "tenant", "variant_id", "image", "image_url", "is_primary"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url


# -------------------------
# PRODUCT VARIANT (INLINE / READ)
# -------------------------

class ProductVariantInlineSerializer(serializers.ModelSerializer):
    measurement_unit = serializers.SerializerMethodField()
    billing_unit = serializers.SerializerMethodField()

    images = VariantImageInlineSerializer(
        many=True,
        read_only=True
    )

    attributes = VariantAttributeInlineSerializer(
        many=True,
        read_only=True
        
    )

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "sku",
            "length",
            "width",
            "height",
            
            "measurement_unit",
            "billing_unit",
            "purchase_price",
            "selling_price",
            "is_active",
            "images",
            "attributes",
        ]

    def get_measurement_unit(self, obj):
        if not obj.measurement_unit:
            return None
        return {
            "id": obj.measurement_unit.id,
            "code": obj.measurement_unit.code,
            "name": obj.measurement_unit.name,
        }

    def get_billing_unit(self, obj):
        if not obj.billing_unit:
            return None
        return {
            "id": obj.billing_unit.id,
            "code": obj.billing_unit.code,
            "name": obj.billing_unit.name,
        }


# -------------------------
# PRODUCT SERIALIZERS
# -------------------------

class ProductListSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    sku = serializers.CharField(read_only=True)

    # Flattened fields for display
    product_type = serializers.CharField(
        source="product_type.name",
        read_only=True
    )
    product_series = serializers.CharField(
        source="product_series.name",
        read_only=True
    )

    # Write fields (for POST/PATCH)
    product_type_id = serializers.PrimaryKeyRelatedField(
        source='product_type',
        queryset=ProductType.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )
    product_series_id = serializers.PrimaryKeyRelatedField(
        source='product_series',
        queryset=ProductSeries.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )

    variants = ProductVariantInlineSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "tenant",
            "name",
            "sku",
            "product_type",
            "product_type_id",
            "product_series",
            "product_series_id",
            "variants",
            "is_active",
            "created_at",
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    sku = serializers.CharField(read_only=True)

    product_type = ProductTypeSerializer(read_only=True)
    product_series = ProductSeriesSerializer(read_only=True)

    variants = ProductVariantInlineSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "tenant",
            "name",
            "sku",
            "product_type",
            "product_series",
            "variants",
            "is_active",
            "created_at",
        ]


# -------------------------
# PRODUCT VARIANT (CRUD)
# -------------------------

class ProductVariantSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    sku = serializers.CharField(read_only=True)

    product_id = serializers.PrimaryKeyRelatedField(
        source="product",
        queryset=Product.objects.all(),
        write_only=True
    )

    measurement_unit_id = serializers.PrimaryKeyRelatedField(
        source="measurement_unit",
        queryset=MeasurementUnit.objects.all(),
        write_only=True,
        allow_null=True,
        required=False
    )

    billing_unit_id = serializers.PrimaryKeyRelatedField(
        source="billing_unit",
        queryset=BillingUnit.objects.all(),
        write_only=True,
        allow_null=True,
        required=False
    )

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "tenant",
            "sku",
            "product_id",
            "length",
            "width",
            "height",
            
            "measurement_unit_id",
            "billing_unit_id",
            "purchase_price",
            "selling_price",
            "is_active",
        ]
        read_only_fields = ("id", "tenant", "sku")

    def validate(self, attrs):
        if attrs.get("purchase_price", 0) < 0:
            raise serializers.ValidationError({"purchase_price": "Must be >= 0"})
        if attrs.get("selling_price", 0) < 0:
            raise serializers.ValidationError({"selling_price": "Must be >= 0"})
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        product = validated_data["product"]

        if request and hasattr(request.user, "tenant"):
            validated_data["tenant"] = request.user.tenant

        validated_data["sku"] = f"{product.sku}-{uuid.uuid4().hex[:4].upper()}"
        return super().create(validated_data)


# -------------------------
# PRODUCT IMAGE SERIALIZER
# -------------------------

class ProductImageSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)

    product_id = serializers.PrimaryKeyRelatedField(
        source="product",
        queryset=Product.objects.all(),
        write_only=True
    )

    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ["id", "tenant", "product_id", "image", "image_url", "is_primary"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url

class ProductWriteSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    sku = serializers.CharField(read_only=True)

    product_type_id = serializers.PrimaryKeyRelatedField(
        source="product_type",
        queryset=ProductType.objects.all(),
        required=False,
        allow_null=True
    )

    product_series_id = serializers.PrimaryKeyRelatedField(
        source="product_series",
        queryset=ProductSeries.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "tenant",
            "name",
            "sku",
            "product_type_id",
            "product_series_id",
            "is_active",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request.user, "tenant"):
            validated_data["tenant"] = request.user.tenant
        return super().create(validated_data)

# catalog/serializers.py
class ProductTemplateSerializer(serializers.ModelSerializer):
    # Select2 needs 'id' and 'text'
    text = serializers.CharField(source='name', read_only=True)

    class Meta:
        model = ProductTemplate
        fields = ['id', 'text', 'sku', 'category'] # Add 'text' 
        
# products1/serializers.py
class ProductBundleSerializer(serializers.ModelSerializer):
    text = serializers.CharField(source='name', read_only=True)
    product_type = serializers.ReadOnlyField(default='standard')

    class Meta:
        model = ProductBundle
        fields = ['id', 'name', 'text', 'product_type', 'description']