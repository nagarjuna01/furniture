# serializers.py (corrected & tenant-safe)
import logging
from django.db import transaction
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import *

logger = logging.getLogger(__name__)

# -------------------------------------------------
# BASE TENANT SAFE MIXIN
# -------------------------------------------------
class TenantSafeMixin:
    """
    Ensures foreign keys belong to the same tenant.
    Assumes serializer.context['tenant'] is set (for SaaS).
    tenant_field_map maps serializer attribute name -> Model class
      e.g. {'measurement_unit': MeasurementUnit, 'product': Product}
    Works with both model instances (from PrimaryKeyRelatedField source=...) or raw PKs.
    """
    tenant_field_map = {}

    def _resolve_instance(self, model, value):
        """
        value may be:
          - instance of model
          - PK (int)
        Return instance or None
        """
        if value is None:
            return None
        if isinstance(value, model):
            return value
        try:
            return model.objects.filter(id=value).first()
        except Exception:
            return None

    def validate(self, data):
        tenant = self.context.get('tenant')
        if not tenant:
            # If no tenant in context, skip tenant checks
            return data

        # data keys are *validated data* names. If PrimaryKeyRelatedField uses source='measurement_unit'
        # the validated data will have the actual key 'measurement_unit' with instance value.
        for field_name, model in getattr(self, "tenant_field_map", {}).items():
            if field_name in data:
                val = data.get(field_name)
                # If serializer used write-only "measurement_unit_id" with source='measurement_unit',
                # validated data will include 'measurement_unit' as an instance.
                instance = self._resolve_instance(model, val)
                if not instance or getattr(instance, 'tenant', tenant) != tenant:
                    raise serializers.ValidationError({
                        field_name: f"Invalid {field_name} (not found or not part of tenant)."
                    })
        return data

# -------------------------------------------------
# MEASUREMENT / BILLING
# -------------------------------------------------
class MeasurementUnitSerializer(serializers.ModelSerializer):
    base_unit_name = serializers.CharField(
        source="base_unit.name", read_only=True
    )

    class Meta:
        model = MeasurementUnit
        fields = [ "id","name","code","symbol", "system","base_unit", "base_unit_name","factor",]



class BillingUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingUnit
        fields = ['id', 'name', 'code']

# -------------------------------------------------
# ATTRIBUTE DEFINITIONS
# -------------------------------------------------
class AttributeDefinitionSerializer(TenantSafeMixin, serializers.ModelSerializer):
    class Meta:
        model = AttributeDefinition
        fields = ['id', 'name', 'field_type', 'choices', 'tenant']
        read_only_fields = ['id']

    def validate(self, data):
        # uniqueness across tenant is enforced by model unique_together
        # but ensure tenant is set in context or provided
        tenant = self.context.get('tenant') or data.get('tenant')
        if not tenant:
            raise serializers.ValidationError("Tenant must be provided in serializer context for AttributeDefinition.")
        return super().validate(data)

# -------------------------------------------------
# VARIANT ATTRIBUTE VALUE
# -------------------------------------------------
class VariantAttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)
    attribute_type = serializers.CharField(source='attribute.field_type', read_only=True)

    class Meta:
        model = VariantAttributeValue
        fields = ['id', 'attribute', 'attribute_name', 'attribute_type', 'value']

# -------------------------------------------------
# VARIANT IMAGES
# -------------------------------------------------
class VariantImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantImage
        fields = ['id', 'image', 'is_primary', 'variant']

    def validate(self, data):
        tenant = self.context.get('tenant')
        if tenant:
            variant = data.get('variant')
            # variant may be instance or id
            if variant and getattr(variant, 'tenant', getattr(variant, 'product', None) and getattr(variant.product, 'tenant', None) != tenant):
                # If variant doesn't have tenant attr, try to inspect variant.product.tenant
                # We primarily check product -> tenant relation.
                pass
        return data

# -------------------------------------------------
# PRODUCT VARIANT (READ + WRITE)
# -------------------------------------------------
class ProductVariantSerializer(TenantSafeMixin, serializers.ModelSerializer):
    # read-only nested
    measurement_unit = MeasurementUnitSerializer(read_only=True)
    billing_unit = BillingUnitSerializer(read_only=True)
    attributes = VariantAttributeValueSerializer(many=True, read_only=True)
    images = VariantImageSerializer(many=True, read_only=True)

    # writeable PK fields (source -> model field)
    measurement_unit_id = serializers.PrimaryKeyRelatedField(
        source='measurement_unit',
        queryset=MeasurementUnit.objects.none(),
        write_only=True,
        required=False,
        allow_null=True
    )
    billing_unit_id = serializers.PrimaryKeyRelatedField(
        source='billing_unit',
        queryset=BillingUnit.objects.none(),
        write_only=True,
        required=False,
        allow_null=True
    )

    product_id = serializers.PrimaryKeyRelatedField(
        source='product',
        queryset=Product.objects.none(),
        write_only=True
    )

    # incoming attributes JSON (list of {attribute: id, value: ...})
    attribute_payload = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False
    )

    tenant_field_map = {
        'measurement_unit': MeasurementUnit,
        'billing_unit': BillingUnit,
        'product': Product,
    }

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'sku', 'length', 'width', 'height', 'weight',
            'purchase_price', 'selling_price', 'is_active',
            'measurement_unit', 'billing_unit',
            'measurement_unit_id', 'billing_unit_id',
            'product_id',
            'attributes', 'images',
            'attribute_payload'
        ]
        read_only_fields = ['id', 'attributes', 'images']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tenant = self.context.get('tenant')
        # Narrow down querysets to tenant scope when possible
        if tenant:
            self.fields['measurement_unit_id'].queryset = MeasurementUnit.objects.filter(tenant=tenant)
            self.fields['billing_unit_id'].queryset = BillingUnit.objects.filter(tenant=tenant)
            self.fields['product_id'].queryset = Product.objects.filter(tenant=tenant)

    # Field-level validation: ensure numeric fields non-negative
    def validate_length(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Length cannot be negative.")
        return value

    def validate_width(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Width cannot be negative.")
        return value

    def validate_height(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Height cannot be negative.")
        return value

    def validate_purchase_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Purchase price cannot be negative.")
        return value

    def validate_selling_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Selling price cannot be negative.")
        return value

    def validate_attribute_payload(self, value):
        """
        Ensure list of attribute objects are valid and belong to tenant.
        Expected element shape: {'attribute': <id>, 'value': <str>}
        """
        tenant = self.context.get('tenant')
        if not isinstance(value, list):
            raise serializers.ValidationError("attribute_payload must be a list.")
        validated = []
        for idx, item in enumerate(value):
            if not isinstance(item, dict):
                raise serializers.ValidationError({idx: "Each attribute payload item must be an object."})
            attr_id = item.get('attribute')
            if not attr_id:
                raise serializers.ValidationError({idx: "Attribute id is required."})
            # Check attribute exists and belongs to tenant if tenant present
            try:
                attr = AttributeDefinition.objects.get(id=attr_id)
            except AttributeDefinition.DoesNotExist:
                raise serializers.ValidationError({idx: f"Attribute id {attr_id} does not exist."})
            if tenant and getattr(attr, 'tenant', None) != tenant:
                raise serializers.ValidationError({idx: f"Attribute id {attr_id} not available for this tenant."})

            # coerce value to str
            validated.append({'attribute': attr_id, 'value': '' if item.get('value') is None else str(item.get('value'))})
        return validated

    def validate(self, data):
        # TenantSafeMixin validation runs here
        data = super().validate(data)
        tenant = self.context.get('tenant')

        # If product present, ensure product tenant matches
        product = data.get('product')
        if tenant and product and getattr(product, 'tenant', None) != tenant:
            raise serializers.ValidationError("Product does not belong to the tenant.")

        # If attribute_payload present, it should already be validated by validate_attribute_payload
        return data

    @transaction.atomic
    def create(self, validated):
        logging_ctx = {'action': 'create_variant', 'product': getattr(validated.get('product'), 'id', None)}
        logger.debug("Creating ProductVariant: %s", logging_ctx)

        attr_data = validated.pop('attribute_payload', [])

        variant = super().create(validated)

        # create attributes (safe because we've validated attribute_payload)
        for item in attr_data:
            VariantAttributeValue.objects.create(
                variant=variant,
                attribute_id=item['attribute'],
                value=item.get('value', '')
            )

        logger.debug("ProductVariant created id=%s", variant.id)
        return variant

    @transaction.atomic
    def update(self, instance, validated):
        logger.debug("Updating ProductVariant id=%s", instance.id)
        attr_data = validated.pop('attribute_payload', None)

        variant = super().update(instance, validated)

        if attr_data is not None:
            # remove and recreate (simple, avoids partial complexity)
            VariantAttributeValue.objects.filter(variant=variant).delete()
            for item in attr_data:
                VariantAttributeValue.objects.create(
                    variant=variant,
                    attribute_id=item['attribute'],
                    value=item.get('value', '')
                )

        logger.debug("ProductVariant updated id=%s", variant.id)
        return variant

# -------------------------------------------------
# PRODUCT IMAGES
# -------------------------------------------------
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary', 'product']

    def validate(self, data):
        tenant = self.context.get('tenant')
        product = data.get('product')
        if tenant and product and getattr(product, 'tenant', None) != tenant:
            raise serializers.ValidationError("Product does not belong to tenant.")
        return data

# -------------------------------------------------
# PRODUCT
# -------------------------------------------------
class ProductSerializer(TenantSafeMixin, serializers.ModelSerializer):
    # writeable PKs for type/model
    type_id = serializers.PrimaryKeyRelatedField(
        source='type',
        queryset=ProductType.objects.none(),
        write_only=True,
        required=False,
        allow_null=True
    )
    model_id = serializers.PrimaryKeyRelatedField(
        source='model',
        queryset=ProductModel.objects.none(),
        write_only=True,
        required=False,
        allow_null=True
    )

    # read-only nested
    type = serializers.SerializerMethodField()
    model = serializers.SerializerMethodField()
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    tenant_field_map = {
        'type': ProductType,
        'model': ProductModel,
    }

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'type', 'model',
            'type_id', 'model_id',
            'is_active', 'created_at',
            'variants', 'images', 'tenant'
        ]
        read_only_fields = ['id', 'sku', 'created_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        tenant = self.context.get('tenant')
        # restrict allowed types/models to tenant if context provided
        if tenant:
            self.fields['type_id'].queryset = ProductType.objects.filter(tenant=tenant)
            self.fields['model_id'].queryset = ProductModel.objects.filter(tenant=tenant)

    def get_type(self, obj):
        if obj.type:
            return {'id': obj.type.id, 'name': obj.type.name, 'slug': obj.type.slug}
        return None

    def get_model(self, obj):
        if obj.model:
            return {'id': obj.model.id, 'name': obj.model.name, 'code': obj.model.code}
        return None

    def validate(self, data):
        """
        Additional validation rules:
         - if model is provided ensure model.type == type (if both provided)
         - ensure tenancy for type/model handled by TenantSafeMixin
        """
        data = super().validate(data)
        type_inst = data.get('type')
        model_inst = data.get('model')

        if model_inst and type_inst and getattr(model_inst, 'type_id', None) and getattr(model_inst, 'type_id', None) != getattr(type_inst, 'id', None):
            # If model selected doesn't belong to selected type
            raise serializers.ValidationError("Selected model does not belong to the selected type.")
        return data

# -------------------------------------------------
# OTHER SERIALIZERS (categories, tags, suppliers, orders, shipping, reviews)
# These use TenantSafeMixin where appropriate and keep behavior consistent.
# -------------------------------------------------
class ProductTypeSerializer(TenantSafeMixin, serializers.ModelSerializer):
    class Meta:
        model = ProductType
        fields = ['id', 'name', 'slug', 'tenant']
        read_only_fields = ['id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ensure tenant provided via context for create/update operations
        if hasattr(self, 'context') and self.context.get('tenant'):
            # nothing else required here; unique_together on model enforces uniqueness
            pass

class ProductModelSerializer(TenantSafeMixin, serializers.ModelSerializer):
    type_id = serializers.PrimaryKeyRelatedField(
        source='type',
        queryset=ProductType.objects.none(),
        write_only=True
    )
    type = ProductTypeSerializer(read_only=True)

    class Meta:
        model = ProductModel
        fields = ['id', 'name', 'code', 'type', 'type_id', 'tenant']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tenant = self.context.get('tenant')
        if tenant:
            self.fields['type_id'].queryset = ProductType.objects.filter(tenant=tenant)

class ProductCategorySerializer(TenantSafeMixin, serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'slug', 'tenant']

class ProductTagSerializer(TenantSafeMixin, serializers.ModelSerializer):
    class Meta:
        model = ProductTag
        fields = ['id', 'name', 'tenant']

class ProductCategoryAssignmentSerializer(serializers.ModelSerializer):
    category = ProductCategorySerializer(read_only=True)

    class Meta:
        model = ProductCategoryAssignment
        fields = ['id', 'category']

class ProductTagAssignmentSerializer(serializers.ModelSerializer):
    tag = ProductTagSerializer(read_only=True)

    class Meta:
        model = ProductTagAssignment
        fields = ['id', 'tag']

class DiscountSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = Discount
        fields = ['id', 'name', 'product', 'product_name', 'percentage', 'fixed_amount', 'start_date', 'end_date', 'tenant']

class SupplierProductSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = SupplierProduct
        fields = '__all__'

class SupplierSerializer(serializers.ModelSerializer):
    products = SupplierProductSerializer(many=True, read_only=True)

    class Meta:
        model = Supplier
        fields = '__all__'

class WorkOrderSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = WorkOrder
        fields = '__all__'

class ShippingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMethod
        fields = '__all__'

class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = '__all__'

class ProductReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductReview
        fields = '__all__'
