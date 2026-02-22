from decimal import Decimal
from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from accounts.models.base import TenantModel
from modular_calc.models import ModularProduct, PartTemplate
from material.models.wood import WoodMaterial
from material.models.edgeband import EdgeBand
from material.models.hardware import Hardware
from customer.models import Client,MarketplaceCustomer

# Industry Standard Conversion
MM2_TO_SQFT = Decimal("0.0000107639")

class QuoteRequest(TenantModel):
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quotes"
    )
    marketplace_customer = models.ForeignKey(
        MarketplaceCustomer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quotes"
    )

    customer_display_name = models.CharField(max_length=255)

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("approved", "Approved"),
        ("locked", "Locked"),
        ("cancelled", "Cancelled"),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft"
    )

    total_cp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_sp = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=18)
    shipping_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    quote_number = models.CharField(max_length=30, unique=True, db_index=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    lead_source = models.CharField(max_length=100, blank=True, null=True)
    is_locked = models.BooleanField(default=False)
    revision_number = models.PositiveIntegerField(default=1)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_quotes"
    )

    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="locked_quotes"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Quote {self.quote_number}"

    def clean(self):
        if not self.client and not self.marketplace_customer:
            raise ValidationError("Either client or marketplace customer is required")
        if self.client and self.marketplace_customer:
            raise ValidationError("Only one customer type is allowed")
        
class QuoteLineItem(TenantModel):
    """
    This is where the Modular vs Standard math happens.
    """
    quote = models.ForeignKey(
        QuoteRequest, 
        related_name="items", 
        on_delete=models.CASCADE
    )
    bundle = models.ForeignKey(
        "products1.ProductBundle", 
        on_delete=models.PROTECT
    )
    variant = models.ForeignKey(
        "products1.ProductVariant", 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL
    )
    quantity = models.PositiveIntegerField(default=1)
    
    # Financial snapshot
    unit_cp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_sp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    line_total_cp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_total_sp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    def save(self, *args, **kwargs):
        # 1. FORCE THE MATH: If price is set, calculate total
        self.line_total_sp = (self.unit_sp or 0) * (self.quantity or 1)
        self.line_total_cp = (self.unit_cp or 0) * (self.quantity or 1)
        
        # 2. SAVE THE RECORD
        super().save(*args, **kwargs)

        # 3. TRIGGER THE EXHAUST: Update the Quote total automatically
        from quoting.services.recalculation import recalc_quote
        recalc_quote(self.quote)
    
class QuoteSolution(TenantModel):
    quote = models.ForeignKey(
        "quoting.QuoteRequest",
        related_name="solutions",
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=255)  
    notes = models.TextField(blank=True)

    total_cp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_sp = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.quote.quote_number} - {self.name}"
class QuoteProduct(TenantModel):
    STATUS_EDITABLE = "editable"
    STATUS_FROZEN = "frozen"

    STATUS_CHOICES = [
        (STATUS_EDITABLE, "Editable"),
        (STATUS_FROZEN, "Frozen"),
    ]
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='children'
    )
    source_type = models.CharField(
        max_length=50, 
        null=True, 
        blank=True,
        help_text="e.g., bundle, bundle_part, modular_part, template"
    )
    solution = models.ForeignKey(QuoteSolution,related_name= "products",on_delete= models.CASCADE,null=True)

    product_template = models.ForeignKey(
        'products1.Product', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL
    )
    product_variant = models.ForeignKey(
        'products1.ProductVariant', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL
    )
    
    # For Modular Products
    modular_product = models.ForeignKey(
        'modular_calc.ModularProduct', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL
    )

    length_mm = models.DecimalField(max_digits=9, decimal_places=2)
    width_mm = models.DecimalField(max_digits=9, decimal_places=2)
    height_mm = models.DecimalField(max_digits=9, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    override_material = models.ForeignKey(
        "material.WoodMaterial",
        null=True, blank=True,
        on_delete=models.SET_NULL
    )
    config_parameters = models.JSONField(default=dict, blank=True)

    total_cp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_sp = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    validated = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_EDITABLE
    )

    frozen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "solution", "product_template"])
        ]

    def __str__(self):
        return f"{self.product_template.name} ({self.length_mm}x{self.width_mm})"

class QuotePart(TenantModel):
    quote_product = models.ForeignKey(
        "quoting.QuoteProduct",
        on_delete=models.CASCADE,
        related_name="parts"
    )

    part_template = models.ForeignKey(
        "modular_calc.PartTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    part_name = models.CharField(max_length=255)

    length_mm = models.DecimalField(max_digits=10, decimal_places=2)
    width_mm = models.DecimalField(max_digits=10, decimal_places=2)
    thickness_mm = models.DecimalField(max_digits=5, decimal_places=2)

    part_qty = models.PositiveIntegerField(default=1)
    grain_direction = models.CharField(max_length=20, default="none")

    material = models.ForeignKey(
        "material.WoodMaterial",
        on_delete=models.PROTECT,
        null=True
    )

    edgeband_top = models.ForeignKey(
        "material.EdgeBand",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+"
    )
    edgeband_bottom = models.ForeignKey(
        "material.EdgeBand",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+"
    )
    edgeband_left = models.ForeignKey(
        "material.EdgeBand",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+"
    )
    edgeband_right = models.ForeignKey(
        "material.EdgeBand",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+"
    )

    total_part_cp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_part_sp = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    two_d_svg_path = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.part_name} ({self.length_mm}x{self.width_mm})"

class QuotePartHardware(TenantModel):
    quote_part = models.ForeignKey(
        "quoting.QuotePart",
        on_delete=models.CASCADE,
        related_name="hardware"
    )

    hardware = models.ForeignKey(
        "material.Hardware",
        on_delete=models.PROTECT
    )

    quantity = models.PositiveIntegerField(default=1)

    unit_cp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_sp = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    total_cp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_sp = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        unique_together = ("tenant", "quote_part", "hardware")

    def __str__(self):
        return f"{self.hardware.name} x {self.quantity}"

class OverrideLog(TenantModel):
    quote_part = models.ForeignKey(
        "quoting.QuotePart",
        on_delete=models.CASCADE,
        related_name="overrides"
    )

    field = models.CharField(max_length=50)
    old_value = models.CharField(max_length=255)
    new_value = models.CharField(max_length=255)
    reason = models.CharField(max_length=255, blank=True)

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]

class QuoteCommunication(TenantModel):
    quote = models.ForeignKey(
        "quoting.QuoteRequest",
        on_delete=models.CASCADE,
        related_name="communications"
    )

    channel = models.CharField(
        max_length=20,
        choices=[
            ("email", "Email"),
            ("whatsapp", "WhatsApp"),
            ("pdf", "PDF"),
        ]
    )

    recipient = models.CharField(max_length=255)

    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    sent_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
class QuoteRevision(TenantModel):
    quote = models.ForeignKey(
        "quoting.QuoteRequest",
        on_delete=models.CASCADE,
        related_name="revisions"
    )

    revision_no = models.PositiveIntegerField()
    snapshot = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tenant", "quote", "revision_no")
        ordering = ["-revision_no"]

