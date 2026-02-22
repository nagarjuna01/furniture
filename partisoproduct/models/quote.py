from accounts.models.base import TenantModel
from django.db import models
from decimal import Decimal
from .material_link import Part1
from .modular import Modular1, HardwareRule
from material.models.wood import WoodMaterial
from material.models.hardware import Hardware

class MvpQuoteRequest(TenantModel):
    customer_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quote {self.pk} for {self.customer_name}"


class MvpQuoteProduct(models.Model):
    quote = models.ForeignKey(MvpQuoteRequest, on_delete=models.CASCADE, related_name='products')
    modular_product = models.ForeignKey(Modular1, on_delete=models.CASCADE)
    length_mm = models.DecimalField(max_digits=10, decimal_places=2)
    width_mm = models.DecimalField(max_digits=10, decimal_places=2)
    height_mm = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.modular_product.name} in Quote {self.quote.pk}"


class MvpQuotePartDetail(models.Model):
    quote_product = models.ForeignKey(MvpQuoteProduct, on_delete=models.CASCADE, related_name='part_details')
    part_template = models.ForeignKey(Part1, on_delete=models.CASCADE)
    part_name = models.CharField(max_length=255)
    selected_material = models.ForeignKey(WoodMaterial, on_delete=models.SET_NULL, null=True, blank=True)
    evaluated_dimensions = models.JSONField(default=dict)
    evaluated_qty = models.PositiveIntegerField()
    evaluated_area = models.DecimalField(max_digits=10, decimal_places=4)
    wastage_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    material_cost = models.DecimalField(max_digits=10, decimal_places=2)
    edge_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hardware_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)

    def save(self, *args, **kwargs):
        self.total_cost = self.material_cost + self.edge_cost + self.hardware_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.part_name} in Quote {self.quote_product.quote.pk}"


class MvpPartHardwareRequirement(models.Model):
    part = models.ForeignKey(Part1, on_delete=models.CASCADE, related_name='hardware_requirements')
    hardware = models.ForeignKey(Hardware, on_delete=models.CASCADE)
    rule = models.ForeignKey(HardwareRule, on_delete=models.CASCADE)
    custom_equation = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('part', 'hardware', 'rule')
        verbose_name = "Part Hardware Requirement"

    def clean(self):
        if self.rule.modular_product != self.part.modular_product:
            from django.core.exceptions import ValidationError
            raise ValidationError("HardwareRule must belong to the same Modular product as the Part")

    def compute_quantity(self):
        from asteval import Interpreter
        aeval = Interpreter()
        context = self.part.quote_product.__dict__  # use quote product dimensions
        context = {k: float(v) for k, v in context.items() if isinstance(v, (int,float,Decimal))}
        aeval.symtable.update(context)

        try:
            if self.rule.is_custom and self.custom_equation:
                return int(aeval(self.custom_equation))
            return int(aeval(self.rule.equation))
        except Exception:
            return 0

    @property
    def thickness(self):
        if hasattr(self.part, 'part_material') and self.part.part_material:
            return self.part.part_material.thickness
        return Decimal('0')
