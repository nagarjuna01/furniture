from django.db import models
from .units import MeasurementUnit, BillingUnit
from .category import Category, CategoryTypes, CategoryModel
from .brand import Brand
from accounts.models.base import TenantModel
from accounts.mixins import TenantSafeMixin


class WoodMaterial(TenantSafeMixin, TenantModel):
    material_grp = models.ForeignKey(Category, on_delete=models.PROTECT)
    material_type = models.ForeignKey(
        CategoryTypes,
        on_delete=models.PROTECT,
        null=True, blank=True
    )
    material_model = models.ForeignKey(
        CategoryModel,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )

    name = models.CharField(max_length=255)
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )

    color = models.CharField(
        max_length=50,
        help_text="Surface color / shade (e.g., Walnut, White, Teak)"
    )

    GRAIN_CHOICES = [
        ("NONE", "No Grain"),
        ("H", "Horizontal"),
        ("V", "Vertical"),
    ]
    grain = models.CharField(
        max_length=10,
        choices=GRAIN_CHOICES,
        default="NONE"
    )

    length_value = models.DecimalField(max_digits=10, decimal_places=3)
    length_unit = models.ForeignKey(
        MeasurementUnit,
        on_delete=models.PROTECT,
        related_name="wood_length_units"
    )

    width_value = models.DecimalField(max_digits=10, decimal_places=3)
    width_unit = models.ForeignKey(
        MeasurementUnit,
        on_delete=models.PROTECT,
        related_name="wood_width_units"
    )

    thickness_value = models.DecimalField(max_digits=10, decimal_places=3)
    thickness_unit = models.ForeignKey(
        MeasurementUnit,
        on_delete=models.PROTECT,
        related_name="wood_thickness_units"
    )

    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_unit = models.ForeignKey(
        BillingUnit,
        on_delete=models.PROTECT,
        related_name="wood_cost_units"
    )

    sell_price = models.DecimalField(max_digits=10, decimal_places=2)
    sell_unit = models.ForeignKey(
        BillingUnit,
        on_delete=models.PROTECT,
        related_name="wood_sell_units"
    )

    is_sheet = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    length_mm = models.DecimalField(max_digits=10, decimal_places=2, editable=False, null=True)
    width_mm = models.DecimalField(max_digits=10, decimal_places=2, editable=False, null=True)
    thickness_mm = models.DecimalField(max_digits=10, decimal_places=2, editable=False, null=True)
    cost_price_sft = models.DecimalField(max_digits=10, decimal_places=2, editable=False, null=True)
    cost_price_panel  = models.DecimalField(max_digits=10, decimal_places=2, editable=False, null=True)
    sell_price_sft =  models.DecimalField(max_digits=10, decimal_places=2, editable=False, null=True)
    sell_price_panel = models.DecimalField(max_digits=10, decimal_places=2, editable=False, null=True)
    class Meta:
        unique_together = (
            "tenant",
            "material_grp",
            "material_type",
            "material_model",
            "name",
            "brand",
            "grain",
        )

    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
        # A. Get the 'MM' Target Unit for normalization
        from material.models import MeasurementUnit
        from material.services.unit_conversion import UnitConversionService
        from material.services.wood_pricing import WoodPricingService
        
        mm_unit = MeasurementUnit.objects.filter(code="MM").first()

        if mm_unit:
            # B. Auto-Convert Dimensions using your Service
            self.length_mm = UnitConversionService.convert(self.length_value, self.length_unit, mm_unit)
            self.width_mm = UnitConversionService.convert(self.width_value, self.width_unit, mm_unit)
            self.thickness_mm = UnitConversionService.convert(self.thickness_value, self.thickness_unit, mm_unit)
        
        try:
            self.cost_price_sft = WoodPricingService.cost_price_per_sft(self)
            self.cost_price_panel = WoodPricingService.cost_price_per_panel(self)
            self.sell_price_sft = WoodPricingService.sell_price_per_sft(self)
            self.sell_price_panel = WoodPricingService.sell_price_per_panel(self)
        except Exception as e:
            # Fallback for Tier 5 safety: Log error or set to 0 to prevent crash
            print(f"Pricing Error: {e}")
        super().save(*args, **kwargs)