from django.db import models, transaction
from accounts.models import TenantModel, GlobalOrTenantModel
from accounts.mixins import TenantSafeMixin
from material.models import MeasurementUnit, BillingUnit

# ==========================================
# 1. CLASSIFICATION & ATTRIBUTES (DNA Layer)
# ==========================================
class ProductType(GlobalOrTenantModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField()

    class Meta:
        unique_together = ("tenant", "slug")
        ordering = ["name"]

    def __str__(self):
        return self.name

class ProductSeries(GlobalOrTenantModel):
    product_type = models.ForeignKey(ProductType, on_delete=models.CASCADE, related_name="series")
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)

    class Meta:
        unique_together = ("tenant", "name")
        ordering = ["name"]

    def __str__(self):
        return f"{self.product_type.name} - {self.name}"

class AttributeDefinition(GlobalOrTenantModel):
    """ Fixes: cannot import name 'AttributeDefinition' """
    FIELD_TYPES = (
        ("text", "Text"),
        ("number", "Number"),
        ("boolean", "Boolean"),
        ("choice", "Choice"),
    )
    name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    choices = models.JSONField(blank=True, default=list)

    class Meta:
        unique_together = ("tenant", "name")
        ordering = ["name"]

    def __str__(self):
        return self.name

# ==========================================
# 2. THE CORE PRODUCT
# ==========================================
class Product(TenantModel):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    
    product_type = models.ForeignKey(ProductType, null=True, blank=True, on_delete=models.SET_NULL, related_name="products")
    product_series = models.ForeignKey(ProductSeries, null=True, blank=True, on_delete=models.SET_NULL, related_name="products")

    is_modular = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ("tenant", "name", "sku")
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

# ==========================================
# 3. VARIANTS & ATTRIBUTE VALUES
# ==========================================
class ProductVariant(TenantModel):
    product = models.ForeignKey(Product, related_name="variants", on_delete=models.CASCADE)
    sku = models.CharField(max_length=100, unique=True)
    
    length = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    width = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    measurement_unit = models.ForeignKey(MeasurementUnit, null=True, blank=True, on_delete=models.SET_NULL)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    billing_unit = models.ForeignKey(BillingUnit, null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.product.name} - {self.sku}"

class VariantAttributeValue(TenantModel):
    variant = models.ForeignKey(ProductVariant, related_name="attributes", on_delete=models.CASCADE)
    attribute = models.ForeignKey(AttributeDefinition, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

    class Meta:
        unique_together = ("tenant", "variant", "attribute")

# ==========================================
# 4. IMAGES (Fixes previous ImportErrors)
# ==========================================
class ProductImage(TenantModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    is_primary = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.is_primary:
                ProductImage.objects.filter(product=self.product, tenant=self.tenant).update(is_primary=False)
            super().save(*args, **kwargs)

class VariantImage(TenantModel):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="variants/")
    is_primary = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.is_primary:
                VariantImage.objects.filter(variant=self.variant, tenant=self.tenant).update(is_primary=False)
            super().save(*args, **kwargs)

# ==========================================
# 5. THE ENGINE BUNDLER
# ==========================================
class ProductBundle(TenantModel, TenantSafeMixin):
    name = models.CharField(max_length=255)
    main_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="bundle_mains")
    addon_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    configuration_data = models.JSONField(
        default=dict, 
        help_text="Stores SVG dimensions and variable overrides (e.g. @ST, @HT)"
    )

# products1/models.py

class ProductTemplate(TenantModel):
    """
    Blueprint for products. Used to quickly create 
    standardized products across different tenants.
    """
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"Template: {self.name}"    

# products1/models.py

class BundleItem(TenantModel):
    bundle = models.ForeignKey(ProductBundle, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('tenant', 'bundle', 'product')