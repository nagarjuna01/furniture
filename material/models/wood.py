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

    class Meta:
        unique_together = (
            "tenant",
            "material_grp",
            "material_type",
            "material_model",
            "name",
            "brand",
        )

    def __str__(self):
        return self.name
