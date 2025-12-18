from django.db import models
#from accounts.models.tenant import Tenant


class MeasurementUnit(models.Model):
    SYSTEM_CHOICES = [
        ("SI", "SI"),
        ("IMPERIAL", "Imperial"),
        ("CUSTOM", "Custom"),
    ]

    # tenant = models.ForeignKey(
    #     "accounts.Tenant",
    #     on_delete=models.CASCADE,
    #     null=True,
    #     blank=True,
    #     related_name="measurement_units"
    # )
    # ↑ Future: tenant-specific custom units

    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20)      # mm, cm, m, in, ft
    symbol = models.CharField(max_length=10, null=True, blank=True)
    system = models.CharField(max_length=10, choices=SYSTEM_CHOICES)

    # Conversion to base unit (example: cm → m = 0.01)
    base_unit = models.ForeignKey(
        "self",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="derived_units"
    )
    factor = models.DecimalField(max_digits=12, decimal_places=6, default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["code"], name="unique_measurement_unit_code")
        ]

    def __str__(self):
        return self.code


class BillingUnit(models.Model):
    # tenant = models.ForeignKey(
    #     "accounts.Tenant",
    #     on_delete=models.CASCADE,
    #     related_name="billing_units"
    # )
    # ↑ Future: tenant-specific billing logic

    name = models.CharField(max_length=50)      # Panel, SFT, PCS, DOZEN
    code = models.CharField(max_length=20)      # pnl, sft, pcs, dz

    # Conversion factor to base billing unit
    # Example:
    #   PCS → factor = 1
    #   DOZEN → factor = 12 (12 pcs)
    factor = models.DecimalField(max_digits=10, decimal_places=4, default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["code"], name="unique_billing_unit_code")
        ]

    def __str__(self):
        return self.code
