import uuid
from django.db import models

# Assumed existing in your material app:
# Material(category, thickness_mm, price_per_sqft, ...)
# EdgeBand(thickness_mm, cost_price_per_mm, ...)
# Hardware(name, sku, cost, ...)
from material.models import WoodEn, EdgeBand, Hardware


class ModularProduct(models.Model):
    """
    Template of a modular product; only expressions & metadata live here.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

    # Python-like expression, validated via safe evaluator
    # Variables available: product_length, product_width, product_height, product_depth, quantity
    product_validation_expression = models.TextField(
        blank=True,
        help_text="e.g., '600 <= product_width <= 2400 and 300 <= product_depth <= 700'"
    )

    # Optional 3D/2D assets at product level
    three_d_asset = models.FileField(upload_to="3d/", blank=True, null=True)  # GLB/GLTF
    two_d_template_svg = models.TextField(blank=True, help_text="SVG template with {{placeholders}}")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PartTemplate(models.Model):
    """
    LAYER 1: Geometry equations; LAYER 2: thickness/edgebands.
    Admin writes equations in terms of product_* and part_thickness.
    """
    product = models.ForeignKey(ModularProduct, on_delete=models.CASCADE, related_name="part_templates")
    name = models.CharField(max_length=255)

    # LAYER 1 (Equations)
    part_length_equation = models.CharField(max_length=255)   # e.g. "product_height"
    part_width_equation  = models.CharField(max_length=255)   # e.g. "product_depth - part_thickness"
    part_qty_equation    = models.CharField(max_length=255, default="1")

    # LAYER 2 (Thickness + edge bands)
    part_thickness_mm = models.DecimalField(max_digits=5, decimal_places=2)  # the driver for material listing
    # Default (admin preselected) edge bands – optional per side
    edgeband_top    = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    edgeband_bottom = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    edgeband_left   = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    edgeband_right  = models.ForeignKey(EdgeBand, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    shape_wastage_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)

    # Optional 3D/2D assets at part level (overrides product assets)
    three_d_asset = models.FileField(upload_to="3d/parts/", blank=True, null=True)  # GLB/GLTF
    two_d_template_svg = models.TextField(blank=True)

    class Meta:
        unique_together = ("product", "name")
        ordering = ["product__name", "name"]

    def __str__(self):
        return f"{self.product.name} / {self.name}"


class PartMaterialWhitelist(models.Model):
    """
    Admin whitelists materials AFTER automatic thickness filtering.
    """
    part_template = models.ForeignKey(PartTemplate, on_delete=models.CASCADE, related_name="material_whitelist")
    material = models.ForeignKey(WoodEn, on_delete=models.CASCADE)
    is_default = models.BooleanField(default=False)

    class Meta:
        unique_together = ("part_template", "material")


class PartEdgeBandWhitelist(models.Model):
    """
    Optional whitelisting for edgebands (auto-suggest thickness ∈ [t..t+5], admin finalizes).
    """
    part_template = models.ForeignKey(PartTemplate, on_delete=models.CASCADE, related_name="edgeband_whitelist")
    edgeband = models.ForeignKey(EdgeBand, on_delete=models.CASCADE)
    is_default = models.BooleanField(default=False)

    class Meta:
        unique_together = ("part_template", "edgeband")


class PartHardwareRule(models.Model):
    """
    LAYER 3: Hardware; quantity by expression.
    Variables: product_* and part_* (length, width, qty) may be used.
    """
    part_template = models.ForeignKey(PartTemplate, on_delete=models.CASCADE, related_name="hardware_rules")
    hardware = models.ForeignKey(Hardware, on_delete=models.CASCADE)
    quantity_equation = models.CharField(max_length=255, default="1")  # e.g., "num_doors * 2", or "part_qty"

    class Meta:
        unique_together = ("part_template", "hardware")

    def __str__(self):
        return f"{self.part_template} -> {self.hardware} ({self.quantity_equation})"
