from django.db import models
from accounts.models.base import TenantModel
#from accounts.models import Tenant

class Brand(TenantModel):
    
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)

    # supplier = models.ForeignKey(
    #     "procurement.Supplier",
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True
    # )
    # ↑ Future: preferred supplier for this brand

    # is_active = models.BooleanField(default=True)
    # ↑ Future: soft-disable brand without deleting

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.upper()
        super().save(*args, **kwargs)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name"],
                name="unique_brand_per_tenant"
            )
        ]
    def __str__(self):
        return self.name
