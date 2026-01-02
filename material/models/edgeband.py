from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal
from accounts.models.base import GlobalOrTenantModel,TenantModel
#from accounts.models import Tenant


class EdgebandName(GlobalOrTenantModel):
    brand = models.ForeignKey(
        'Brand',
        on_delete=models.CASCADE,
        related_name='edgeband_names'
    )
    depth = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Depth in mm (e.g. 2.00)"
    )
    name = models.CharField(
        max_length=255,
        editable=False
        # Ensure uniqueness across brand + depth
    )
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Combine brand name + depth for display
        if self.brand:
            self.name = f"{self.brand.name} {self.depth}mm"
        else:
            self.name = f"UNKNOWN {self.depth}mm"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class EdgeBand(TenantModel):
    edgeband_name = models.ForeignKey(
        EdgebandName,
        on_delete=models.CASCADE,
        related_name="variants"
    )

    # thickness is optional in some vendors
    thickness = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Edge band thickness in mm"
    )

    # Pricing → RUNNING METER ONLY
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Cost price per running meter"
    )

    sell_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Selling price per running meter"
    )

    wastage_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Expected wastage percentage"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = (
            "tenant",
            "edgeband_name",
            
            "thickness"
        )

    def clean(self):
        if self.cost_price < 0:
            raise ValidationError("Cost price cannot be negative.")
        if self.sell_price < 0:
            raise ValidationError("Sell price cannot be negative.")
        if self.wastage_pct < 0:
            raise ValidationError("Wastage cannot be negative.")

    @property
    def margin_price(self):
        return (self.cost_price * Decimal("1.20")).quantize(Decimal("0.01"))

    def __str__(self):
        return f"{self.edgeband_name}"
