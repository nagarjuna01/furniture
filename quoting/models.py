from decimal import Decimal
from django.db import models, transaction
from modular_calc.models import ModularProduct, PartTemplate, PartMaterialWhitelist, PartEdgeBandWhitelist, PartHardwareRule
from material.models import WoodEn, EdgeBand, Hardware
from modular_calc.utils import build_context, eval_expr, validate_product
from django.conf import settings

MM2_TO_SQFT = Decimal("0.0000107639")


class QuoteRequest(models.Model):
    customer_name = models.CharField(max_length=255)
    created_by = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Quote {self.pk} - {self.customer_name}"


class QuoteProduct(models.Model):
    quote = models.ForeignKey(QuoteRequest, on_delete=models.CASCADE, related_name="products")
    product_template = models.ForeignKey(ModularProduct, on_delete=models.CASCADE)

    length_mm  = models.DecimalField(max_digits=9, decimal_places=2)
    width_mm   = models.DecimalField(max_digits=9, decimal_places=2)
    height_mm  = models.DecimalField(max_digits=9, decimal_places=2)
    depth_mm   = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    quantity   = models.PositiveIntegerField(default=1)

    # cache validation status
    validated = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["quote", "product_template"])
        ]

    def __str__(self):
        return f"{self.product_template.name} (Q{self.quote_id})"

    @property
    def description(self):
        return f"{self.product_template.name} | L{self.length_mm} W{self.width_mm} H{self.height_mm} D{self.depth_mm} | Qty {self.quantity}"

    def as_dims(self) -> dict:
        return {
            "product_length": float(self.length_mm),
            "product_width":  float(self.width_mm),
            "product_height": float(self.height_mm),
            "product_depth":  float(self.depth_mm),
            "quantity":       float(self.quantity),
        }

    def validate_inputs(self):
        self.validated = validate_product(self.product_template.product_validation_expression, self.as_dims())
        return self.validated

    @transaction.atomic
    def expand_to_parts(self, allow_non_whitelisted_override=False):
        """
        Generate QuotePart + QuotePartHardware rows from PartTemplates.
        LAYER 1..3 fully resolved. LAYER 4..5 fields are ready for costing later.
        """
        # cleanup to re-generate
        self.parts.all().delete()

        dims = self.as_dims()
        for pt in self.product_template.part_templates.select_related().all():
            ctx = build_context(dims, part_thickness=float(pt.part_thickness_mm))

            # LAYER 1: equations
            length = Decimal(str(eval_expr(pt.part_length_equation, ctx))).quantize(Decimal("0.01"))
            width  = Decimal(str(eval_expr(pt.part_width_equation, ctx))).quantize(Decimal("0.01"))
            qty    = int(eval_expr(pt.part_qty_equation, ctx))

            # LAYER 2: pick default material by whitelist (same thickness) & default edge bands
            default_mat = (PartMaterialWhitelist.objects
                           .filter(part_template=pt, is_default=True)
                           .select_related("material")
                           .first())
            material = default_mat.material if default_mat else None

            # Edge bands: if whitelisted present default, else use saved on part (optional)
            default_edges = (PartEdgeBandWhitelist.objects
                             .filter(part_template=pt, is_default=True)
                             .select_related("edgeband"))
            edge_dict = {"top": pt.edgeband_top, "bottom": pt.edgeband_bottom,
                         "left": pt.edgeband_left, "right": pt.edgeband_right}
            for e in default_edges:
                # override any side if you prefer a single default
                edge_dict["top"] = edge_dict["top"] or e.edgeband

            # Create QuotePart
            qp = QuotePart.objects.create(
                quote_product=self,
                part_template=pt,
                part_name=pt.name,
                thickness_mm=pt.part_thickness_mm,
                length_mm=length,
                width_mm=width,
                part_qty=qty,
                shape_wastage_multiplier=pt.shape_wastage_multiplier,
                material=material,
                edgeband_top=edge_dict["top"],
                edgeband_bottom=edge_dict["bottom"],
                edgeband_left=edge_dict["left"],
                edgeband_right=edge_dict["right"],
            )

            # LAYER 3: hardware
            for h in pt.hardware_rules.select_related("hardware").all():
                h_ctx = build_context(dims, part_thickness=float(pt.part_thickness_mm), extras={
                    "part_length": float(length),
                    "part_width": float(width),
                    "part_qty": float(qp.part_qty),
                })
                h_qty = int(eval_expr(h.quantity_equation, h_ctx))
                QuotePartHardware.objects.create(
                    quote_part=qp,
                    hardware=h.hardware,
                    quantity=h_qty
                )

        return self.parts.count()


class QuotePart(models.Model):
    """
    Captures the resolved part instance under a QuoteProduct.
    """
    quote_product = models.ForeignKey(QuoteProduct, on_delete=models.CASCADE, related_name="parts")
    part_template = models.ForeignKey(PartTemplate, on_delete=models.PROTECT)
    part_name = models.CharField(max_length=255)

    # LAYER 1 (resolved geometry)
    length_mm = models.DecimalField(max_digits=9, decimal_places=2)
    width_mm  = models.DecimalField(max_digits=9, decimal_places=2)
    part_qty  = models.PositiveIntegerField(default=1)

    # LAYER 2 (thickness + edge bands)
    thickness_mm = models.DecimalField(max_digits=5, decimal_places=2)
    material = models.ForeignKey(WoodEn, on_delete=models.SET_NULL, null=True, blank=True)
    # employee override tracking
    override_by_employee = models.BooleanField(default=False)
    override_reason = models.CharField(max_length=255, blank=True)

    edgeband_top    = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    edgeband_bottom = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    edgeband_left   = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    edgeband_right  = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    shape_wastage_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)

    # LAYER 4 (associated material calc cache)
    # area in mm^2 per part (before wastage) x qty
    area_mm2 = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    area_sqft = models.DecimalField(max_digits=12, decimal_places=4, default=0)

    # LAYER 5 (cutting/making charges – values to be filled by costing service)
    cutting_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    making_charges  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost      = models.DecimalField(max_digits=12, decimal_places=2, default=0)

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
    """
    Track employee overrides for audit.
    """
    quote_part = models.ForeignKey(QuotePart, on_delete=models.CASCADE, related_name="overrides")
    field = models.CharField(max_length=50)   # "material" / "thickness" / "edgeband"
    old_value = models.CharField(max_length=255)
    new_value = models.CharField(max_length=255)
    reason = models.CharField(max_length=255, blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
