from django.db import models
from django.db.models import Q


# =========================
# Timestamp base
# =========================
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ("-created_at",)


# =========================
# Tenant-aware queryset
# =========================
class TenantQuerySet(models.QuerySet):
    def for_tenant(self, tenant):
        if tenant is None:
            raise ValueError("Tenant must be provided")
        return self.filter(tenant=tenant)


class TenantManager(models.Manager):
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)

    def for_tenant(self, tenant):
        return self.get_queryset().for_tenant(tenant)


# =========================
# Strict tenant model
# =========================
class TenantModel(TimeStampedModel):
    """
    Data ALWAYS belongs to a tenant.
    No global access allowed.
    """
    tenant = models.ForeignKey(
        "accounts.Tenant",
        on_delete=models.CASCADE,
        related_name="%(class)s_set",
        db_index=True,
    )

    objects = TenantManager()

    class Meta:
        abstract = True


# =========================
# Global OR tenant-scoped
# =========================
class GlobalOrTenantQuerySet(models.QuerySet):
    def for_tenant(self, tenant):
        """
        Returns tenant-specific records first,
        falls back to global (tenant=None).
        """
        if tenant is None:
            return self.filter(tenant__isnull=True)

        return self.filter(
            Q(tenant=tenant) | Q(tenant__isnull=True)
        )

    def global_only(self):
        return self.filter(tenant__isnull=True)


class GlobalOrTenantModel(TimeStampedModel):
    """
    Data can be global (tenant=None)
    or tenant-specific.
    """
    tenant = models.ForeignKey(
        "accounts.Tenant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="%(class)s_set",
        db_index=True,
    )

    objects = GlobalOrTenantQuerySet.as_manager()

    class Meta:
        abstract = True
