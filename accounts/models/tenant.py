from django.db import models
from accounts.models.base import TimeStampedModel


class Tenant(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        TRIAL = "trial", "Trial"
        EXPIRED = "expired", "Expired"

    name = models.CharField(max_length=100, unique=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TRIAL,
        db_index=True,
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
