# accounts/mixins.py

from django.core.exceptions import ValidationError
import uuid
from .models import Tenant


class TenantSafeViewSetMixin:
    """
    Ensures queryset is filtered by tenant.
    Superusers see all objects.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return qs.none()

        if user.is_superuser:
            return qs

        if not getattr(user, "tenant", None):
            return qs.none()

        return qs.filter(tenant=user.tenant)

    def perform_create(self, serializer):
        user = self.request.user

        # ---------------- SUPERUSER ----------------
        if user.is_superuser:
            tenant = getattr(user, "tenant", None) or Tenant.objects.first()
            instance = serializer.save(tenant=tenant)

        # ---------------- NORMAL USER --------------
        else:
            tenant = user.tenant
            instance = serializer.save(tenant=tenant)

        # ---------------- SKU GENERATION (POST SAVE) ----------------
        if instance.__class__.__name__ == "Product" and not instance.sku:
            instance.sku = f"PRD-{tenant.id}-{uuid.uuid4().hex[:6].upper()}"
            instance.save(update_fields=["sku"])
        assert instance.tenant, "Tenant must always be set on tenant-owned models"



from django.core.exceptions import ValidationError
from django.db import models


class TenantSafeMixin(models.Model):
    """
    Prevents cross-tenant FK assignments for tenant-owned models.
    Only checks FKs that ALSO have a tenant field.
    """

    class Meta:
        abstract = True

    def clean(self):
        super().clean()

        tenant = getattr(self, "tenant", None)
        if not tenant:
            return

        for field in self._meta.fields:
            if not isinstance(field, models.ForeignKey):
                continue

            related_obj = getattr(self, field.name, None)
            if not related_obj:
                continue

            # Only enforce if related model ALSO has tenant
            if hasattr(related_obj, "tenant"):
                if related_obj.tenant != tenant:
                    raise ValidationError({
                        field.name: (
                            f"{field.name} belongs to a different tenant."
                        )
                    })
