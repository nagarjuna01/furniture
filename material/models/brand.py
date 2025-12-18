from django.db import models
#from accounts.models import Tenant

class Brand(models.Model):
    # tenant = models.ForeignKey(
    #     "accounts.Tenant",
    #     on_delete=models.CASCADE,
    #     related_name="brands"
    # )
    # ↑ Future: multi-tenant brand separation

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

    def __str__(self):
        return self.name
