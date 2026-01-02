from django.db import models
from accounts.models.base import TenantModel,GlobalOrTenantModel
#from accounts.models.tenant import Tenant


class MeasurementUnit(GlobalOrTenantModel):
    SYSTEM_CHOICES = [
        ("SI", "SI"),
        ("IMPERIAL", "Imperial"),
        ("CUSTOM", "Custom"),
    ]

    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20)
    symbol = models.CharField(max_length=10, null=True, blank=True)
    system = models.CharField(max_length=10, choices=SYSTEM_CHOICES)

    base_unit = models.ForeignKey(
        "self",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="derived_units"
    )
    factor = models.DecimalField(max_digits=12, decimal_places=6, default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "code"],
                name="uq_measurement_unit_tenant_code"
            )
        ]

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        self.name = self.name.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code



class BillingUnit(GlobalOrTenantModel):

    name = models.CharField(max_length=50)      # Panel, SFT, PCS, DOZEN
    code = models.CharField(max_length=20)      # pnl, sft, pcs, dz

    # Conversion factor to base billing unit
    # Example:
    #   PCS → factor = 1
    #   DOZEN → factor = 12 (12 pcs)
    factor = models.DecimalField(max_digits=10, decimal_places=4, default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "code"],
                name="uq_billing_unit_tenant_code"
            )
        ]
    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        self.name = self.name.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code
