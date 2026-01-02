from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation
from .brand import Brand
from accounts.models.base import GlobalOrTenantModel,TenantModel
#from accounts.models import Tenant

class HardwareGroup(GlobalOrTenantModel):
    name = models.CharField(max_length=50, unique=True)  
            
    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
        # Ensure the name is uppercase
        self.name = self.name.upper()
        super().save(*args, **kwargs)

class Hardware(TenantModel):
    h_group = models.ForeignKey(
        HardwareGroup,
        on_delete=models.CASCADE,
        related_name="hardware_items"
    )

    h_name = models.CharField(max_length=50)

    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # ✅ USE BillingUnit (pcs, set, dozen, box)
    billing_unit = models.ForeignKey(
        "material.BillingUnit",
        on_delete=models.PROTECT,
        related_name="hardware_items"
    )

    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    sell_price = models.DecimalField(max_digits=10, decimal_places=2)

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = (
           "tenant",
            "h_group",
            "h_name",
            "brand"
        )

    def save(self, *args, **kwargs):
        self.h_name = self.h_name.upper()
        super().save(*args, **kwargs)
