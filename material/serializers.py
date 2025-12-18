from rest_framework import serializers
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from .models.wood import WoodMaterial
from .models.edgeband import EdgeBand, EdgebandName
from .models.hardware import Hardware, HardwareGroup
from .models.brand import Brand
from .models.category import Category, CategoryTypes, CategoryModel
from .models.units import MeasurementUnit, BillingUnit


# -------------------------------
# Brand Serializer with duplicate check
# -------------------------------
class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "tenant", "name", "is_active"]

    def validate_name(self, value):
        tenant = self.initial_data.get("tenant")
        qs = Brand.objects.filter(name__iexact=value)
        if tenant:
            qs = qs.filter(tenant=tenant)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(f"Brand with name '{value}' already exists.")
        return value


# -------------------------------
# MeasurementUnit Serializer
# -------------------------------
class MeasurementUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementUnit
        fields = ["id", "tenant", "name", "code", "symbol", "system", "factor"]

    def validate_name(self, value):
        tenant = self.initial_data.get("tenant")
        qs = MeasurementUnit.objects.filter(name__iexact=value)
        if tenant:
            qs = qs.filter(tenant=tenant)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(f"MeasurementUnit with name '{value}' already exists.")
        return value

    def validate_code(self, value):
        tenant = self.initial_data.get("tenant")
        qs = MeasurementUnit.objects.filter(code__iexact=value)
        if tenant:
            qs = qs.filter(tenant=tenant)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(f"MeasurementUnit with code '{value}' already exists.")
        return value


# -------------------------------
# BillingUnit Serializer
# -------------------------------
class BillingUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingUnit
        fields = ["id", "tenant", "name", "code", "factor"]

    def validate_name(self, value):
        tenant = self.initial_data.get("tenant")
        qs = BillingUnit.objects.filter(name__iexact=value)
        if tenant:
            qs = qs.filter(tenant=tenant)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(f"BillingUnit with name '{value}' already exists.")
        return value

    def validate_code(self, value):
        tenant = self.initial_data.get("tenant")
        qs = BillingUnit.objects.filter(code__iexact=value)
        if tenant:
            qs = qs.filter(tenant=tenant)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(f"BillingUnit with code '{value}' already exists.")
        return value


# -------------------------------
# Category Serializer
# -------------------------------
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "tenant", "name"]

    def validate_name(self, value):
        tenant = self.initial_data.get("tenant")
        qs = Category.objects.filter(name__iexact=value)
        if tenant:
            qs = qs.filter(tenant=tenant)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(f"Category with name '{value}' already exists.")
        return value


# -------------------------------
# CategoryTypes Serializer
# -------------------------------
class CategoryTypesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryTypes
        fields = ["id", "tenant", "category", "name"]

    def validate(self, attrs):
        category = attrs.get("category") or self.instance.category
        name = attrs.get("name") or self.instance.name
        qs = CategoryTypes.objects.filter(category=category, name__iexact=name)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(f"CategoryType '{name}' already exists for this category.")
        return attrs


# -------------------------------
# CategoryModel Serializer
# -------------------------------
class CategoryModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryModel
        fields = ["id", "tenant", "model_category", "name"]

    def validate(self, attrs):
        model_category = attrs.get("model_category") or self.instance.model_category
        name = attrs.get("name") or self.instance.name
        qs = CategoryModel.objects.filter(model_category=model_category, name__iexact=name)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(f"CategoryModel '{name}' already exists for this category type.")
        return attrs

# -------------------------------
# WoodMaterial Serializer
# -------------------------------
class WoodMaterialSerializer(serializers.ModelSerializer):
    material_grp = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    material_type = serializers.PrimaryKeyRelatedField(queryset=CategoryTypes.objects.all(), allow_null=True, required=False)
    material_model = serializers.PrimaryKeyRelatedField(queryset=CategoryModel.objects.all(), allow_null=True, required=False)
    brand = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all(), allow_null=True, required=False)

    length_unit = serializers.PrimaryKeyRelatedField(queryset=MeasurementUnit.objects.all())
    width_unit = serializers.PrimaryKeyRelatedField(queryset=MeasurementUnit.objects.all())
    thickness_unit = serializers.PrimaryKeyRelatedField(queryset=MeasurementUnit.objects.all())

    cost_unit = serializers.PrimaryKeyRelatedField(queryset=BillingUnit.objects.all())
    sell_unit = serializers.PrimaryKeyRelatedField(queryset=BillingUnit.objects.all())

    class Meta:
        model = WoodMaterial
        fields = [
            "id", "tenant", "material_grp", "material_type", "material_model",
            "name", "brand",
            "length_value", "length_unit",
            "width_value", "width_unit",
            "thickness_value", "thickness_unit",
            "cost_price", "cost_unit",
            "sell_price", "sell_unit",
            "is_sheet",
        ]

    def validate_name(self, value):
        tenant = self.initial_data.get("tenant")
        if WoodMaterial.objects.filter(tenant=tenant, name__iexact=value).exists():
            raise serializers.ValidationError(f"WoodMaterial with name '{value}' already exists for this tenant.")
        return value

    def _convert_to_mm(self, value, unit):
        """Convert length/width/thickness to mm using factor."""
        factor = getattr(unit, "factor", None)
        if factor is None:
            raise ValidationError(f"Unit {unit} has no conversion factor.")
        return Decimal(value) * Decimal(factor)

    def _calculate_prices(self, instance):
        """
        Store derived prices in panel and sqft equivalents.
        Example:
            - cost_price: panel
            - cost_price_sft: calculated from dimensions
        """
        length_mm = instance.length_value
        width_mm = instance.width_value

        # Area in square feet
        area_sft = (length_mm / Decimal("304.8")) * (width_mm / Decimal("304.8"))

        # Panel vs SFT cost
        instance.cost_price_sft = (instance.cost_price / area_sft).quantize(Decimal("0.01")) if area_sft else instance.cost_price
        instance.sell_price_sft = (instance.sell_price / area_sft).quantize(Decimal("0.01")) if area_sft else instance.sell_price

    @transaction.atomic
    def create(self, validated_data):
        # Convert units to mm for storage
        validated_data["length_value"] = self._convert_to_mm(validated_data["length_value"], validated_data["length_unit"])
        validated_data["width_value"] = self._convert_to_mm(validated_data["width_value"], validated_data["width_unit"])
        validated_data["thickness_value"] = self._convert_to_mm(validated_data["thickness_value"], validated_data["thickness_unit"])

        instance = super().create(validated_data)
        self._calculate_prices(instance)
        instance.save()
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        # Convert units to mm for storage
        if "length_value" in validated_data:
            instance.length_value = self._convert_to_mm(validated_data.pop("length_value"), validated_data.pop("length_unit"))
        if "width_value" in validated_data:
            instance.width_value = self._convert_to_mm(validated_data.pop("width_value"), validated_data.pop("width_unit"))
        if "thickness_value" in validated_data:
            instance.thickness_value = self._convert_to_mm(validated_data.pop("thickness_value"), validated_data.pop("thickness_unit"))

        # Update remaining fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Recalculate derived prices
        self._calculate_prices(instance)
        instance.save()
        return instance


# -------------------------------
# EdgeBand Serializer
# -------------------------------

class EdgebandNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = EdgebandName
        fields = [
            "id",
            "tenant",
            "depth",
            "name",
            "is_active",
        ]
        read_only_fields = ("name", "tenant")

    def validate(self, attrs):
        tenant = self.context["request"].user.tenant
        depth = attrs.get("depth")

        if EdgebandName.objects.filter(
            tenant=tenant, depth=depth
        ).exists():
            raise serializers.ValidationError(
                {"depth": "Edgeband with this depth already exists"}
            )
        return attrs

    def create(self, validated_data):
        validated_data["tenant"] = self.context["request"].user.tenant
        return super().create(validated_data)
    

class EdgeBandSerializer(serializers.ModelSerializer):
    edgeband_name = serializers.PrimaryKeyRelatedField(queryset=EdgebandName.objects.all())
    brand = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all(), allow_null=True)

    class Meta:
        model = EdgeBand
        fields = [
            "id", "tenant", "edgeband_name", "brand", "thickness",
            "cost_price", "sell_price", "wastage_pct", "is_active"
        ]

    def validate(self, attrs):
        if attrs.get("cost_price", 0) < 0:
            raise serializers.ValidationError("Cost price cannot be negative.")
        if attrs.get("sell_price", 0) < 0:
            raise serializers.ValidationError("Sell price cannot be negative.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        instance = super().create(validated_data)
        # Calculate margin price automatically
        instance.sell_price = instance.cost_price * Decimal("1.2")
        instance.save()
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.sell_price = instance.cost_price * Decimal("1.2")
        instance.save()
        return instance


# -------------------------------
# Hardware Serializer
# -------------------------------
class HardwareGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = HardwareGroup
        fields = ["id", "tenant", "name", "is_active"]
        read_only_fields = ("tenant",)

    def validate_name(self, value):
        tenant = self.context["request"].user.tenant
        if HardwareGroup.objects.filter(
            tenant=tenant, name__iexact=value
        ).exists():
            raise serializers.ValidationError("Hardware group already exists")
        return value

    def create(self, validated_data):
        validated_data["tenant"] = self.context["request"].user.tenant
        return super().create(validated_data)

class HardwareSerializer(serializers.ModelSerializer):
    h_group = serializers.PrimaryKeyRelatedField(queryset=HardwareGroup.objects.all())
    brand = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all(), allow_null=True)

    class Meta:
        model = Hardware
        fields = [
            "id", "tenant", "h_group", "h_name", "brand",
            "unit", "p_price", "s_price"
        ]

    def validate(self, attrs):
        if attrs.get("p_price", 0) < 0 or attrs.get("s_price", 0) < 0:
            raise serializers.ValidationError("Hardware prices cannot be negative.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.s_price = instance.p_price * Decimal("1.2")  # margin
        instance.save()
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.s_price = instance.p_price * Decimal("1.2")  # margin
        instance.save()
        return instance
