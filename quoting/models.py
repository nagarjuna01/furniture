from decimal import Decimal
from django.db import models, transaction
from django.conf import settings

from accounts.models.base import TenantModel
from modular_calc.models import ModularProduct, PartTemplate
from material.models.wood import WoodMaterial
from material.models.edgeband import EdgeBand
from material.models.hardware import Hardware

# Industry Standard Conversion
MM2_TO_SQFT = Decimal("0.0000107639")

class QuoteRequest(TenantModel):
    customer_name = models.CharField(max_length=255)
    
    STATUS_CHOICES = [
        ('draft', 'Draft/Preview'),
        ('sent', 'Sent to Customer'),
        ('approved', 'Approved for Production'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    total_cp = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Total Factory Cost")
    total_sp = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Total Selling Price (Pre-Tax)")
    
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=18.0)
    shipping_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    @property
    def tax_amount(self) -> Decimal:
        return (self.total_sp * (self.tax_percentage / Decimal("100"))).quantize(Decimal("1.00"))

    @property
    def grand_total(self) -> Decimal:
        return self.total_sp + self.tax_amount + self.shipping_charges

    def refresh_totals(self):
        """Aggregate totals from all products in this quote."""
        totals = self.products.aggregate(
            cp=models.Sum("total_cp"),
            sp=models.Sum("total_sp")
        )
        self.total_cp = totals["cp"] or Decimal("0.00")
        self.total_sp = totals["sp"] or Decimal("0.00")
        self.save(update_fields=["total_cp", "total_sp"])

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Quote {self.pk} - {self.customer_name}"


class QuoteProduct(TenantModel):
    quote = models.ForeignKey(QuoteRequest, on_delete=models.CASCADE, related_name="products")
    product_template = models.ForeignKey(ModularProduct, on_delete=models.PROTECT)

    length_mm = models.DecimalField(max_digits=9, decimal_places=2)
    width_mm = models.DecimalField(max_digits=9, decimal_places=2)
    height_mm = models.DecimalField(max_digits=9, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    override_material = models.ForeignKey(WoodMaterial, on_delete=models.SET_NULL, null=True, blank=True)
    config_parameters = models.JSONField(default=dict, blank=True)

    total_sp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    validated = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["tenant", "quote", "product_template"])]

    def __str__(self):
        return f"{self.product_template.name} ({self.length_mm}x{self.width_mm})"

    def as_dims(self) -> dict:
        return {
            "product_length": float(self.length_mm),
            "product_width": float(self.width_mm),
            "product_height": float(self.height_mm),
            "quantity": float(self.quantity),
        }

    def get_final_context(self) -> dict:
        from accounts.models import GlobalVariable
        context = self.as_dims()
        globals_dict = {v.abbr: float(v.value) for v in GlobalVariable.objects.filter(tenant=self.tenant)}
        context.update(globals_dict)
        context.update(self.config_parameters) 
        return context

    def evaluate_now(self):
        from modular_calc.evaluation.product_engine import ProductEngine
        engine = ProductEngine(self.product_template)
        full_ctx = self.get_final_context()
        # Pass context twice (as dims and as params) to ensure logic resolves
        return engine.evaluate(full_ctx, parameters=full_ctx)

    @transaction.atomic
    def expand_to_parts(self):
        """Creates QuotePart records based on current evaluation."""
        self.parts.all().delete()
        evaluation = self.evaluate_now()
        
        prod_cp = Decimal("0.00")
        prod_sp = Decimal("0.00")

        for p_data in evaluation.get("parts", []):
            qp_part = QuotePart.objects.create(
                tenant=self.tenant,
                quote_product=self,
                part_template=p_data.get("template_obj"),
                part_name=p_data["name"],
                length_mm=Decimal(str(p_data["length"])),
                width_mm=Decimal(str(p_data["width"])),
                part_qty=int(p_data["quantity"]),
                thickness_mm=Decimal(str(p_data["thickness"])),
                material=p_data.get("material_obj"),
                edgeband_top=p_data["edgeband_objs"].get("top"),
                edgeband_bottom=p_data["edgeband_objs"].get("bottom"),
                edgeband_left=p_data["edgeband_objs"].get("left"),
                edgeband_right=p_data["edgeband_objs"].get("right"),
                total_part_cp=Decimal(str(p_data.get("total_cost", 0))),
                total_part_sp=Decimal(str(p_data.get("total_price", 0))),
                two_d_svg_path=p_data.get("two_d_svg", "")
            )

            for hw_item in p_data.get("hardware", []):
                hw_obj = hw_item["obj"]
                QuotePartHardware.objects.create(
                    tenant=self.tenant,
                    quote_part=qp_part,
                    hardware=hw_obj,
                    quantity=hw_item["quantity"],
                    unit_cp=hw_obj.cost_price,
                    unit_sp=hw_obj.selling_price
                )
            
            prod_cp += qp_part.total_part_cp
            prod_sp += qp_part.total_part_sp

        self.total_cp = prod_cp
        self.total_sp = prod_sp
        self.validated = True
        self.save()
        self.quote.refresh_totals()
        return self.parts.count()


class QuotePart(TenantModel):
    quote_product = models.ForeignKey(QuoteProduct, on_delete=models.CASCADE, related_name="parts")
    part_template = models.ForeignKey(PartTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    part_name = models.CharField(max_length=255)

    length_mm = models.DecimalField(max_digits=10, decimal_places=2)
    width_mm = models.DecimalField(max_digits=10, decimal_places=2)
    part_qty = models.PositiveIntegerField(default=1)
    thickness_mm = models.DecimalField(max_digits=5, decimal_places=2)
    grain_direction = models.CharField(max_length=20, default='none')

    material = models.ForeignKey(WoodMaterial, on_delete=models.PROTECT, null=True)
    edgeband_top = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    edgeband_bottom = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    edgeband_left = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    edgeband_right = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    
    total_part_cp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_part_sp = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    two_d_svg_path = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.part_name} ({self.length_mm}x{self.width_mm})"


class QuotePartHardware(TenantModel):
    quote_part = models.ForeignKey(QuotePart, on_delete=models.CASCADE, related_name="hardware")
    hardware = models.ForeignKey(Hardware, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

    unit_cp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_sp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    total_cp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_sp = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        unique_together = ("tenant", "quote_part", "hardware")

    def save(self, *args, **kwargs):
        self.total_cp = self.unit_cp * Decimal(str(self.quantity))
        self.total_sp = self.unit_sp * Decimal(str(self.quantity))
        super().save(*args, **kwargs)


class OverrideLog(TenantModel):
    quote_part = models.ForeignKey(QuotePart, on_delete=models.CASCADE, related_name="overrides")
    field = models.CharField(max_length=50)
    old_value = models.CharField(max_length=255)
    new_value = models.CharField(max_length=255)
    reason = models.CharField(max_length=255, blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]