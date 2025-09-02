from rest_framework import serializers
from drf_yasg.utils import swagger_serializer_method
import datetime
from django.db import transaction # <-- Import this for atomic operations
from .models import (
    Product, ProductType, ProductModel, BillingUnit, MeasurementUnit,
    ProductVariant, ProductImage, VariantImage, AttributeDefinition, VariantAttributeValue
)


class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = ['id', 'name', 'slug']


class ProductModelSerializer(serializers.ModelSerializer):
    type = ProductTypeSerializer(read_only=True)
    type_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductType.objects.all(), source='type', write_only=True)

    class Meta:
        model = ProductModel
        fields = ['id', 'name', 'code', 'type', 'type_id']


class BillingUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingUnit
        fields = ['id', 'name', 'code']


class MeasurementUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementUnit
        fields = ['id', 'name', 'code']

class AttributeDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeDefinition
        fields = ['id', 'name', 'field_type', 'choices']
        extra_kwargs = {
            'choices': {'required': False}
        }

# Re-enabled and updated for handling 'id' for updates/deletes
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary']
        extra_kwargs = {
            'id': {'read_only': False, 'required': False}, # Allow 'id' for updates/deletes
            'image': {'required': False} # Image is not always required for updates (e.g., if only changing is_primary)
        }


# Re-enabled and updated for handling 'id' for updates/deletes
class VariantImageSerializer(serializers.ModelSerializer):
    variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all())

    class Meta:
        model = VariantImage
        fields = ['id', 'variant', 'image', 'is_primary']
        extra_kwargs = {
            'id': {'read_only': False, 'required': False},
            'image': {'required': True},  # Required when uploading
        }
    
# Re-enabled and updated for handling 'id' for updates/deletes
class VariantAttributeValueSerializer(serializers.ModelSerializer):
    attribute_id = serializers.PrimaryKeyRelatedField(
        queryset=AttributeDefinition.objects.all(), write_only=True, source='attribute')
    attribute = AttributeDefinitionSerializer(read_only=True)
    class Meta:
        model = VariantAttributeValue
        fields = ['id','attribute','attribute_id','value']
        extra_kwargs = {
            'id': {'read_only': False, 'required': False},
            'value': {'required': False}
        }

# ProductVariantSerializer: Re-enabled nested fields and fixed create/update methods
class ProductVariantSerializer(serializers.ModelSerializer):
    sku = serializers.CharField(read_only=True)
    # Re-enabled nested writable fields
    attributes = VariantAttributeValueSerializer(many=True, required=False)
    images = VariantImageSerializer(many=True, read_only=True)

    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )

    measurement_unit = MeasurementUnitSerializer(read_only=True)
    billing_unit = BillingUnitSerializer(read_only=True)

    measurement_unit_id = serializers.PrimaryKeyRelatedField(
        queryset=MeasurementUnit.objects.all(), source='measurement_unit', write_only=True
    )
    billing_unit_id = serializers.PrimaryKeyRelatedField(
        queryset=BillingUnit.objects.all(), source='billing_unit', write_only=True
    )

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'sku', 'length', 'width', 'height',
            'measurement_unit', 'measurement_unit_id',
            'billing_unit', 'billing_unit_id',
            'purchase_price', 'selling_price',
            'attributes', 'images', # <-- Re-enabled these fields
            'product_id',
        ]

    

    @transaction.atomic # Ensure atomicity
    def create(self, validated_data):
        attributes_data = validated_data.pop('attributes', [])
        images_data = validated_data.pop('images', [])

        product_instance = validated_data.get("product")

        attr_code = ''.join(
            (attr.get("value", "")[:2] or "XX").upper()
            for attr in attributes_data
        ) or "GEN"

        timestamp = datetime.datetime.now().strftime('%M%S')
        validated_data["sku"] = f"{product_instance.sku}-{attr_code}{timestamp}"

        variant = ProductVariant.objects.create(**validated_data)

        for attr_data in attributes_data:
            VariantAttributeValue.objects.create(variant=variant, **attr_data)

        for img_data in images_data:
            VariantImage.objects.create(variant=variant, **img_data) # Note: 'variant' field set here

        return variant

    @transaction.atomic # Ensure atomicity
    def update(self, instance, validated_data):
        attributes_data = validated_data.pop('attributes', None)
        images_data = validated_data.pop('images', None)

        # Update main ProductVariant fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if attributes_data is not None:
            existing_attribute_values = {attr.id: attr for attr in instance.attributes.all()}
            incoming_attribute_ids = {data.get('id') for data in attributes_data if data.get('id')}

            # Delete attributes not in the incoming data
            for attr_id, attr_obj in existing_attribute_values.items():
                if attr_id not in incoming_attribute_ids:
                    attr_obj.delete() # Delete the actual object

            # Update or create attributes
            for attr_data in attributes_data:
                attr_id = attr_data.get('id')
                if attr_id: # Existing attribute
                    attr_obj = existing_attribute_values.get(attr_id)
                    if attr_obj: # Ensure it belongs to this variant
                        # Update fields
                        attr_obj.attribute = attr_data.get('attribute', attr_obj.attribute) # 'attribute' here is the object from PrimaryKeyRelatedField source
                        attr_obj.value = attr_data.get('value', attr_obj.value)
                        attr_obj.save()
                    # else: The ID was provided but not found for this variant, implying an error or bad ID.
                    # You might want to log this or raise an error.
                else: # New attribute (no ID provided)
                    VariantAttributeValue.objects.create(variant=instance, **attr_data)

        return instance


# ProductSerializer: Re-enabled nested fields and fixed create/update methods
class ProductSerializer(serializers.ModelSerializer):
    type = ProductTypeSerializer(read_only=True)
    type_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductType.objects.all(), source='type', write_only=True)

    model = ProductModelSerializer(read_only=True)
    model_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductModel.objects.all(), source='model', write_only=True,
        allow_null=True, required=False)

    sku = serializers.CharField(read_only=True)

    # Re-enabled variants_data for read-only display
    variants_data = serializers.SerializerMethodField(read_only=True)

    # Re-enabled images for writable nested behavior
    images = ProductImageSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'type', 'type_id', 'model', 'model_id',
            'is_active', 'created_at',
            'variants_data', # <-- Re-enabled
            'images',        # <-- Re-enabled
        ]
        ref_name = 'Products1AppProductSerializer'

    def get_variants_data(self, obj):
        # Ensure ProductVariantSerializer is properly defined and doesn't cause circular imports
        # if it also tries to nest ProductSerializer.
        return ProductVariantSerializer(obj.variants.all(), many=True, context=self.context).data

    @transaction.atomic # Ensure atomicity
    def create(self, validated_data):
        images_data = validated_data.pop('images', []) # Pop nested image data

        product = Product.objects.create(**validated_data) # Create the main product

        # Create associated ProductImage instances
        for img_data in images_data:
            ProductImage.objects.create(product=product, **img_data)

        return product

    @transaction.atomic # Ensure atomicity
    def update(self, instance, validated_data):
        images_data = validated_data.pop('images', None) # Pop nested image data

        # Update the main Product instance fields
        # This loop handles all direct fields of the Product model
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save() # Save the main product instance

        # Handle nested images update/creation/deletion
        if images_data is not None:
            existing_image_ids = [img.id for img in instance.images.all()]
            incoming_image_ids = [data.get('id') for data in images_data if data.get('id')]

            # Delete images not present in the incoming data
            for img_id in existing_image_ids:
                if img_id not in incoming_image_ids:
                    # Consider actual file deletion from storage here if not handled by signals
                    ProductImage.objects.filter(id=img_id).delete()

            # Create new images or update existing ones
            for img_data in images_data:
                img_id = img_data.get('id')
                if img_id: # If ID is present, it's an existing image to potentially update
                    img_obj = ProductImage.objects.get(id=img_id, product=instance)
                    # For images, if a new 'image' file is provided, it replaces the old one.
                    # We iterate and set attributes.
                    for key, value in img_data.items():
                        setattr(img_obj, key, value)
                    img_obj.save()
                else: # If no ID, it's a new image to create
                    ProductImage.objects.create(product=instance, **img_data)

        return instance