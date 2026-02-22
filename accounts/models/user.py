from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from accounts.models.base import TimeStampedModel


class User(AbstractUser, TimeStampedModel):
    """
    Tenant-aware user.
    Superusers and system users (guardian anonymous) can bypass tenant constraints.
    """
    tenant = models.ForeignKey(
        "accounts.Tenant",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users"
    )

    def save(self, *args, **kwargs):
        # ✅ Allow django-guardian anonymous user
        if self.username == getattr(settings, "ANONYMOUS_USER_NAME", "AnonymousUser"):
            return super().save(*args, **kwargs)

        # ✅ Enforce tenant only for real users
        if not self.is_superuser and self.tenant is None:
            raise ValueError("Tenant must be set for non-superusers")

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
