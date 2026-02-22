from django.db import models
from accounts.models.base import TenantModel
from django.utils import timezone

class GlobalVariable(TenantModel):
    CATEGORY_CHOICES = [
        ('THICKNESS', 'Material Thickness'),
        ('GAP', 'Construction Gaps'),
        ('OFFSET', 'Hardware Offsets'),
        ('METAL', 'Metal Profiles'),
    ]

    tenant = models.ForeignKey(
        'accounts.Tenant',
        on_delete=models.CASCADE,
        related_name='global_variables'
    )
    name = models.CharField(max_length=100, help_text="e.g., Standard Side Thickness")
    abbr = models.CharField(max_length=10, help_text="e.g., @ST")
    value = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='THICKNESS')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('tenant', 'abbr')
        ordering = ('category', 'name')

    def __str__(self):
        return f"{self.abbr} ({self.value})"
