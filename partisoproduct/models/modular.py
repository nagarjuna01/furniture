import uuid
from django.db import models
from accounts.models.base import GlobalOrTenantModel
PRODUCT_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('active', 'Active'),
    ('archived', 'Archived'),
]

class Modular1(GlobalOrTenantModel):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=255, unique=True)

    product_validation_expression = models.TextField(
        null=True, blank=True,
        help_text="Use product_length, product_width, product_height for validation."
    )

    status = models.CharField(
        max_length=20, choices=PRODUCT_STATUS_CHOICES,
        default='draft'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_parts(self):
        return self.parts.all()

    def get_constraints_dict(self):
        return {c.abbreviation: float(c.value) for c in self.product_parameters.all()}

    class Meta:
        verbose_name = "Modular Product"
        verbose_name_plural = "Modular Products"


class Constraint(GlobalOrTenantModel):
    modular_product = models.ForeignKey(Modular1, on_delete=models.CASCADE, related_name='product_parameters')
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=20)
    value = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('modular_product', 'abbreviation')
        verbose_name = "Product Parameter"
        verbose_name_plural = "Product Parameters"

    def __str__(self):
        return f"{self.abbreviation} = {self.value}"


class HardwareRule(GlobalOrTenantModel):
    modular_product = models.ForeignKey(Modular1, on_delete=models.CASCADE, related_name='hardware_rules')
    name = models.CharField(max_length=100, help_text="e.g. '2 per door'")
    equation = models.CharField(max_length=255, help_text="e.g. 'num_doors * 2'")
    is_custom = models.BooleanField(default=False)

    class Meta:
        unique_together = ('modular_product', 'name')
        verbose_name = "Hardware Rule"
        verbose_name_plural = "Hardware Rules"

    def __str__(self):
        return self.name

class AttractiveCosts(GlobalOrTenantModel):
    typeofcost = models.CharField(max_length=100)
    
    # Store the equation as a string instead of a hardcoded number
    cost_equation = models.CharField(max_length=255, help_text="Equation to calculate the cost (e.g., 'product_length * 0.5')")
    
    # This field will store the calculated result after evaluation
    cost = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)
    
    def __str__(self):
        return self.typeofcost