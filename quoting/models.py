from decimal import Decimal
from django.db import models, transaction
from django.conf import settings
from modular_calc.models import ModularProduct, PartTemplate
from material.models.wood import WoodMaterial
from material.models.edgeband import EdgeBand
from material.models.hardware import Hardware
from modular_calc.evaluation.part_evaluator import PartEvaluator

MM2_TO_SQFT = Decimal("0.0000107639")


class QuoteRequest(models.Model):
    customer_name = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Quote {self.pk} - {self.customer_name}"


class QuoteProduct(models.Model):
    quote = models.ForeignKey(QuoteRequest, on_delete=models.CASCADE, related_name="products")
    product_template = models.ForeignKey(ModularProduct, on_delete=models.CASCADE)

    length_mm = models.DecimalField(max_digits=9, decimal_places=2)
    width_mm = models.DecimalField(max_digits=9, decimal_places=2)
    height_mm = models.DecimalField(max_digits=9, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    validated = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["quote", "product_template"])
        ]

    def __str__(self):
        return f"{self.product_template.name} (Q{self.quote_id})"

    @property
    def description(self):
        return (
            f"{self.product_template.name} | "
            f"L{self.length_mm} W{self.width_mm} H{self.height_mm} | Qty {self.quantity}"
        )

    def as_dims(self) -> dict:
        """Return product dimensions for part evaluation context."""
        return {
            "product_length": float(self.length_mm),
            "product_width": float(self.width_mm),
            "product_height": float(self.height_mm),
            "quantity": float(self.quantity),
        }

    @transaction.atomic
    def expand_to_parts(self, parameters=None):
        """
        Generate QuotePart + QuotePartHardware rows using PartEvaluator.
        """
        self.parts.all().delete()
        product_dims = self.as_dims()
        parameters = parameters or {}

        for pt in self.product_template.part_templates.all():
            evaluator = PartEvaluator(pt, product_dims, parameters)
            part_data = evaluator.evaluate()

            qp = QuotePart.objects.create(
                quote_product=self,
                part_template=pt,
                part_name=part_data["name"],
                length_mm=part_data["length"],
                width_mm=part_data["width"],
                part_qty=int(part_data["quantity"]),
                thickness_mm=part_data["thickness"],
                shape_wastage_multiplier=part_data["shape_wastage_multiplier"],
                material=part_data["material_obj"],
                edgeband_top=part_data["edgeband_objs"].get("top"),
                edgeband_bottom=part_data["edgeband_objs"].get("bottom"),
                edgeband_left=part_data["edgeband_objs"].get("left"),
                edgeband_right=part_data["edgeband_objs"].get("right"),
            )

            # Create QuotePartHardware
            for hardware_rule in pt.hardware_rules.select_related("hardware").all():
                h_qty = int(part_data["quantity"] * hardware_rule.quantity_equation)
                QuotePartHardware.objects.create(
                    quote_part=qp,
                    hardware=hardware_rule.hardware,
                    quantity=h_qty
                )

        return self.parts.count()


class QuotePart(models.Model):
    quote_product = models.ForeignKey(QuoteProduct, on_delete=models.CASCADE, related_name="parts")
    part_template = models.ForeignKey(PartTemplate, on_delete=models.PROTECT)
    part_name = models.CharField(max_length=255)

    length_mm = models.DecimalField(max_digits=9, decimal_places=2)
    width_mm = models.DecimalField(max_digits=9, decimal_places=2)
    part_qty = models.PositiveIntegerField(default=1)

    thickness_mm = models.DecimalField(max_digits=5, decimal_places=2)
    material = models.ForeignKey(WoodMaterial, on_delete=models.SET_NULL, null=True, blank=True)
    override_by_employee = models.BooleanField(default=False)
    override_reason = models.CharField(max_length=255, blank=True)

    edgeband_top = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    edgeband_bottom = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    edgeband_left = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    edgeband_right = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    shape_wastage_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)

    area_mm2 = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    area_sqft = models.DecimalField(max_digits=12, decimal_places=4, default=0)

    cutting_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    making_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def compute_area(self):
        mm2 = (self.length_mm * self.width_mm) * self.part_qty * self.shape_wastage_multiplier
        self.area_mm2 = mm2
        self.area_sqft = (mm2 * MM2_TO_SQFT).quantize(Decimal("0.0001"))

    def save(self, *args, **kwargs):
        if not self.area_mm2 or not self.area_sqft:
            self.compute_area()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.part_name} ({self.length_mm}x{self.width_mm}x{self.thickness_mm}) x {self.part_qty}"


class QuotePartHardware(models.Model):
    quote_part = models.ForeignKey(QuotePart, on_delete=models.CASCADE, related_name="hardware")
    hardware = models.ForeignKey(Hardware, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("quote_part", "hardware")


class OverrideLog(models.Model):
    quote_part = models.ForeignKey(QuotePart, on_delete=models.CASCADE, related_name="overrides")
    field = models.CharField(max_length=50)
    old_value = models.CharField(max_length=255)
    new_value = models.CharField(max_length=255)
    reason = models.CharField(max_length=255, blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
