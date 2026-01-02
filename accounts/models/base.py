# accounts.models.base.py
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantModel(TimeStampedModel):
    tenant = models.ForeignKey(
        "accounts.Tenant",
        on_delete=models.CASCADE,
        related_name="%(class)ss"
    )

    class Meta:
        abstract = True


class GlobalOrTenantModel(TimeStampedModel):
    tenant = models.ForeignKey(
        "accounts.Tenant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="%(class)ss"
    )

    class Meta:
        abstract = True
