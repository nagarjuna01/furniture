from rest_framework import serializers
from decimal import Decimal,ROUND_HALF_UP
from django.db import transaction
from django.core.exceptions import ValidationError

from .models.wood import WoodMaterial
from .models.edgeband import EdgeBand, EdgebandName
from .models.hardware import Hardware, HardwareGroup
from .models.brand import Brand
from .models.category import Category, CategoryTypes, CategoryModel
from .models.units import MeasurementUnit, BillingUnit
from .services.billing_conversion import BillingConversionService,BillingConversionError
from .services.unit_conversion import UnitConversionService

# -------------------------------
# Brand Serializer with duplicate check
# -------------------------------
class BrandSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)

    class Meta:
        model = Brand
        fields = ["id", "name", "description", "tenant_name"]
        read_only_fields = ["id", "tenant_name"]

    def validate_name(self, value):
        user = self.context["request"].user
        tenant = getattr(user, "tenant", None)
        qs = Brand.objects.filter(tenant=tenant, name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                f"Brand '{value}' already exists for your tenant."
            )
        return value


# -------------------------------
# MeasurementUnit Serializer
# -------------------------------
class MeasurementUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementUnit
        fields = ["id", "name", "code", "symbol", "system", "factor", "tenant"]
        read_only_fields = ["tenant"]

    def create(self, validated_data):
        validated_data["tenant"] = self.context["request"].user.tenant
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["tenant"] = instance.tenant
        return super().update(instance, validated_data)
    def validate(self, attrs):
        code = attrs.get("code", "").upper()
        system = attrs.get("system")

        qs = MeasurementUnit.objects.filter(
            code__iexact=code,
            tenant=self.context["request"].user.tenant
        )

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                {"code": "Measurement unit code already exists."}
            )

        return attrs

class BillingUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingUnit
        fields = ["id", "name", "code", "factor"]

    def validate(self, attrs):
        tenant = self.context["request"].user.tenant

        qs = BillingUnit.objects.filter(
            tenant=tenant,
            name__iexact=attrs["name"],
            code__iexact=attrs["code"],
        )

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Billing unit with same name and code already exists."
            )

        if attrs.get("factor", 1) <= 0:
            raise serializers.ValidationError(
                {"factor": "Factor must be greater than zero"}
            )

        return attrs

    def create(self, validated_data):
        validated_data["tenant"] = self.context["request"].user.tenant
        return super().create(validated_data)


# -------------------------------
# Category Serializer
# -------------------------------
class CategorySerializer(serializers.ModelSerializer):
    tenant_id = serializers.IntegerField(source="tenant.id", read_only=True)
    tenant_name = serializers.CharField(source="tenant.name", read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "tenant_id", "tenant_name"]
        read_only_fields = ["id", "tenant_id", "tenant_name"]

    def validate_name(self, value):
        qs = Category.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(f"Category '{value}' already exists.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get("request")
        
        if request and not request.user.is_superuser:
            tenant = getattr(request.user, "tenant", None)
            if not tenant:
                raise serializers.ValidationError("Current user has no tenant assigned.")
            validated_data["tenant"] = tenant
        elif "tenant" not in validated_data:
            raise serializers.ValidationError("Tenant must be specified.")

        return super().create(validated_data)


# -------------------------------
# CategoryTypes Serializer
# -------------------------------
class CategoryTypesSerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(source="category.name", read_only=True)
    tenant_id = serializers.IntegerField(source="category.tenant.id", read_only=True)
    tenant_name = serializers.CharField(source="category.tenant.name", read_only=True)

    # FK input
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    class Meta:
        model = CategoryTypes
        fields = ["id", "category", "category_label", "name", "tenant_id", "tenant_name"]
        read_only_fields = ["id", "category_label", "tenant_id", "tenant_name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and not request.user.is_superuser:
            self.fields["category"].queryset = Category.objects.filter(tenant=request.user.tenant)

    def validate(self, attrs):
        qs = CategoryTypes.objects.filter(
            category=attrs["category"],
            name__iexact=attrs["name"]
        )
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "CategoryType already exists for this category."
            )
        return attrs

# -------------------------------
# CategoryModel Serializer
# -------------------------------
class CategoryModelSerializer(serializers.ModelSerializer):
    model_category_label = serializers.CharField(source="model_category.name", read_only=True)
    tenant_id = serializers.IntegerField(source="model_category.category.tenant.id", read_only=True)
    tenant_name = serializers.CharField(source="model_category.category.tenant.name", read_only=True)

    # FK input
    model_category = serializers.PrimaryKeyRelatedField(queryset=CategoryTypes.objects.all())

    class Meta:
        model = CategoryModel
        fields = ["id", "model_category", "model_category_label", "name", "tenant_id", "tenant_name"]
        read_only_fields = ["id", "model_category_label", "tenant_id", "tenant_name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and not request.user.is_superuser:
            self.fields["model_category"].queryset = CategoryTypes.objects.filter(
                category__tenant=request.user.tenant
            )

    def validate(self, attrs):
        qs = CategoryModel.objects.filter(
            model_category=attrs["model_category"],
            name__iexact=attrs["name"]
        )
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "CategoryModel already exists for this category type."
            )
        return attrs
from material.services.wood_pricing import WoodPricingService
# -------------------------------
# WoodMaterial Serializer
# -------------------------------
class WoodMaterialSerializer(serializers.ModelSerializer):
    # ---------- FK inputs ----------
    material_grp = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all()
    )
    
    material_type = serializers.PrimaryKeyRelatedField(
        queryset=CategoryTypes.objects.all(),
        allow_null=True, required=False
    )
    
    material_model = serializers.PrimaryKeyRelatedField(
        queryset=CategoryModel.objects.all(),
        allow_null=True, required=False
    )
    
    brand = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(),
        allow_null=True, required=False
    )
    grain_label = serializers.CharField(
        source="get_grain_display",
        read_only=True
    )

    length_unit = serializers.PrimaryKeyRelatedField(
        queryset=MeasurementUnit.objects.all()
    )
    
    width_unit = serializers.PrimaryKeyRelatedField(
        queryset=MeasurementUnit.objects.all()
    )
    thickness_unit = serializers.PrimaryKeyRelatedField(
        queryset=MeasurementUnit.objects.all()
    )

    cost_unit = serializers.PrimaryKeyRelatedField(
        queryset=BillingUnit.objects.all()
    )
    sell_unit = serializers.PrimaryKeyRelatedField(
        queryset=BillingUnit.objects.all()
    )
    material_grp_label = serializers.CharField(source="material_grp.name", read_only=True)
    material_type_label = serializers.CharField(source="material_type.name", read_only=True)
    material_model_label = serializers.CharField(source="material_model.name", read_only=True)
    brand_label = serializers.CharField(source="brand.name", read_only=True)

    
    # ---------- Tenant readonly ----------
    tenant_id = serializers.IntegerField(
        source="tenant.id", read_only=True
    )
    tenant_name = serializers.CharField(
        source="tenant.name", read_only=True
    )

    class Meta:
        model = WoodMaterial
        fields = [
            "id",
            "material_grp",
            "material_type",
            "material_model",
            "name",
            "brand",
            "brand_label",
            "grain",
            "grain_label",
            "material_grp_label",
            "material_type_label",
            "material_model_label",
            "length_value", "length_unit",
            "width_value", "width_unit",
            "thickness_value", "thickness_unit",
            "cost_price", "cost_unit",
            "sell_price", "sell_unit",
            "is_sheet",
            "is_active",
            "length_mm",
            "width_mm",
            "thickness_mm",
            "cost_price_sft",
            "cost_price_panel",
            "sell_price_sft",
            "sell_price_panel",
            "tenant_id",
            "tenant_name",
        ]

        read_only_fields = (
            "tenant_id",
            "tenant_name",
            "brand_label",
            "material_grp_label",
            "material_type_label",
            "material_model_label",
            "grain_label",
            "length_mm",
            "width_mm",
            "thickness_mm",
            "cost_price_sft",
            "cost_price_panel",
            "sell_price_sft",
            "sell_price_panel",
        )

        extra_kwargs = {
            "name": {"validators": []},  # 🔥 disables name-only uniqueness
        }

        validators = [
            serializers.UniqueTogetherValidator(
                queryset=WoodMaterial.objects.all(),
                fields=[
                    
                    "material_grp",
                    "material_type",
                    "material_model",
                    "name",
                    "brand",
                    "grain",
                ],
                message="Material with this combination already exists."
            )
        ]

# -------------------------------
# EdgeBand Serializer
# -------------------------------

def round_decimal(value):
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

class EdgebandNameSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source="brand.name", read_only=True)

    class Meta:
        model = EdgebandName
        fields = ["id", "brand", "brand_name", "depth", "name", "is_active"]
        read_only_fields = ["name"]
   

class EdgeBandSerializer(serializers.ModelSerializer):
    edgeband_name = serializers.PrimaryKeyRelatedField(
        queryset=EdgebandName.objects.all()
    )
    

    min_price = serializers.SerializerMethodField(read_only=True)

    edgeband_name_label = serializers.CharField(
        source="edgeband_name.name",
        read_only=True
    )
    depth = serializers.DecimalField(
        source="edgeband_name.depth", 
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )

    tenant_id = serializers.IntegerField(
        source="tenant.id",
        read_only=True
    )
    tenant_name = serializers.CharField(
        source="tenant.name",
        read_only=True
    )

    class Meta:
        model = EdgeBand
        fields = [
            "id",
            "edgeband_name",
            
            "thickness",
            "cost_price",
            "sell_price",
            "wastage_pct",
            "min_price",
            "edgeband_name_label",
            "depth",
            "tenant_id",
            "tenant_name",
            "is_active",
        ]
        read_only_fields = (
            "tenant",
            "tenant_id",
            "tenant_name",
            "min_price",
            "depth",
        )

    def get_min_price(self, obj):
        wastage = obj.wastage_pct or Decimal("0")
        factor = (
            Decimal("1.20") *
            (Decimal("1.00") + (wastage / Decimal("100")))
        )
        return (obj.cost_price * factor).quantize(Decimal("0.01"))

    def validate(self, attrs):
        if attrs.get("cost_price", 0) < 0:
            raise serializers.ValidationError("Cost price cannot be negative.")
        if attrs.get("sell_price", 0) < 0:
            raise serializers.ValidationError("Sell price cannot be negative.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        user = request.user

        if not user.is_superuser:
            validated_data["tenant"] = user.tenant

        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

    

# -------------------------------
# Hardware Serializer
# -------------------------------
class HardwareGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = HardwareGroup
        fields = ["id", "name"]
        read_only_fields = ("id",)

    def validate_name(self, value):
        tenant = self.context["request"].user.tenant

        qs = HardwareGroup.objects.filter(
            tenant=tenant,
            name__iexact=value
        )

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError("Hardware group already exists")

        return value


    def create(self, validated_data):
        validated_data["tenant"] = self.context["request"].user.tenant
        return super().create(validated_data)


class HardwareSerializer(serializers.ModelSerializer):
    h_group = serializers.PrimaryKeyRelatedField(
        queryset=HardwareGroup.objects.all()
    )
    brand = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(),
        allow_null=True,
        required=False
    )
    billing_unit = serializers.PrimaryKeyRelatedField(
        queryset=BillingUnit.objects.all()
    )
    sl_price = serializers.SerializerMethodField()
    
    tenant_id = serializers.IntegerField(source="tenant.id", read_only=True)
    tenant_name = serializers.CharField(source="tenant.name", read_only=True)
    h_group_label = serializers.CharField(source="h_group.name", read_only=True)
    brand_label = serializers.CharField(source="brand.name", read_only=True)
    billing_unit_code = serializers.CharField(source="billing_unit.code", read_only=True)
    class Meta:
        model = Hardware
        fields = [
            "id",
            "h_group",
            "h_name",
            "brand",
            "billing_unit",
            "cost_price",
            "sell_price",
            "sl_price",
            "tenant_id",
            "tenant_name",
            "h_group_label",
            "brand_label",
            "billing_unit_code",
            "is_active",
        ]
        read_only_fields = ("id", "sl_price", "tenant_id", "tenant_name","h_group_label","brand_label","billing_unit_code")

    def get_sl_price(self, obj):
        # Display cost_price * 1.20 as optional calculation
        if obj.cost_price is not None:
            return (obj.cost_price * Decimal("1.20")).quantize(Decimal("0.01"))
        return None

    def validate(self, attrs):
        if attrs.get("cost_price", 0) < 0:
            raise serializers.ValidationError({"cost_price": "Cannot be negative"})
        if attrs.get("sell_price", 0) < 0:
            raise serializers.ValidationError({"sell_price": "Cannot be negative"})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        user = request.user
        if not user.is_superuser:
            validated_data["tenant"] = user.tenant
        validated_data.pop("sl_price", None)
        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        validated_data.pop("sl_price", None)
        return super().update(instance, validated_data)
