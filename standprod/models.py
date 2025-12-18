from django.db import models
from django.core.exceptions import ValidationError
import datetime

# ---------------------------
# TENANT & MODULE MANAGEMENT
# ---------------------------
class Tenant(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class TenantModule(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='modules')
    module_name = models.CharField(max_length=100)
    is_enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = ('tenant', 'module_name')


# ---------------------------
# PRODUCT CATALOG
# ---------------------------
class ProductType(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='product_types')
    name = models.CharField(max_length=100)
    slug = models.SlugField()

    class Meta:
        unique_together = ('tenant', 'name')

    def __str__(self):
        return self.name

class ProductModel(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='product_models')
    type = models.ForeignKey(ProductType, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)

    class Meta:
        unique_together = ('tenant', 'code')

    def __str__(self):
        return f"{self.type.name} - {self.name}"



class MeasurementUnit(models.Model):
    SYSTEM_CHOICES = [("SI", "SI (Metric)"),("IMPERIAL", "Imperial"),("CUSTOM", "Custom"),]

    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20,null=True,blank=True)          # e.g. m, cm, in
    symbol = models.CharField(max_length=10,null=True, blank=True)        # same as code usually
    system = models.CharField(max_length=10, choices=SYSTEM_CHOICES)

    # base unit within same system (cm → m)
    base_unit = models.ForeignKey("self",null=True,blank=True,on_delete=models.SET_NULL,related_name="derived_units")
    factor = models.DecimalField(max_digits=12, decimal_places=6, default=1 )
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True,blank=True)

    class Meta:
        unique_together = [
            ("tenant", "code"),
            ("tenant", "name"),
        ]

    def __str__(self):
        return f"{self.name} ({self.symbol})"



class BillingUnit(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='billing_units')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)

    class Meta:
        unique_together = ('tenant', 'code')

    def __str__(self):
        return self.code


class Product(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    type = models.ForeignKey(ProductType, null=True, blank=True, on_delete=models.SET_NULL)
    model = models.ForeignKey(ProductModel, null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.sku:
            now = datetime.datetime.now()
            name_part = (self.name[:3] if self.name else "PRD").upper()
            type_part = (self.type.name[:2] if self.type else "TP").upper()
            model_part = (self.model.name[:2] if self.model else "BP").upper()
            timestamp = now.strftime('%m%d%M%S')
            self.sku = f"{name_part}{type_part}{model_part}{timestamp}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    sku = models.CharField(max_length=100, unique=True)
    length = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    width = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    measurement_unit = models.ForeignKey(MeasurementUnit, null=True, blank=True, on_delete=models.SET_NULL)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    billing_unit = models.ForeignKey(BillingUnit, null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)

    def clean(self):
        if Product.objects.filter(sku=self.sku).exists():
            raise ValidationError("This SKU already exists at the product level.")

    def __str__(self):
        return f"{self.product.name} ({self.length}x{self.width}x{self.height})"


class AttributeDefinition(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='attribute_definitions')
    name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=[
        ('text', 'Text'),
        ('number', 'Number'),
        ('boolean', 'Boolean'),
        ('choice', 'Choice'),
    ])
    choices = models.JSONField(blank=True, default=list)

    class Meta:
        unique_together = ('tenant', 'name')

    def __str__(self):
        return self.name


class VariantAttributeValue(models.Model):
    variant = models.ForeignKey(ProductVariant, related_name='attributes', on_delete=models.CASCADE)
    attribute = models.ForeignKey(AttributeDefinition, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

    class Meta:
        unique_together = ('variant', 'attribute')


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    is_primary = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_primary:
            ProductImage.objects.filter(product=self.product).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} Image"


class VariantImage(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='variants/')
    is_primary = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_primary:
            VariantImage.objects.filter(variant=self.variant).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.variant.sku} Image"


# ---------------------------
# CATEGORIES & TAGS
# ---------------------------
class ProductCategory(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    slug = models.SlugField()

    class Meta:
        unique_together = ('tenant', 'name')

    def __str__(self):
        return self.name


class ProductTag(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('tenant', 'name')

    def __str__(self):
        return self.name


class ProductCategoryAssignment(models.Model):
    product = models.ForeignKey(Product, related_name='categories', on_delete=models.CASCADE)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)


class ProductTagAssignment(models.Model):
    product = models.ForeignKey(Product, related_name='tags', on_delete=models.CASCADE)
    tag = models.ForeignKey(ProductTag, on_delete=models.CASCADE)


# ---------------------------
# DISCOUNTS & PROMOTIONS
# ---------------------------
class Discount(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='discounts')
    name = models.CharField(max_length=100)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.CASCADE)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    fixed_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.name} ({self.product})"


# ---------------------------
# SUPPLIERS
# ---------------------------
class Supplier(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='suppliers')
    name = models.CharField(max_length=255)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class SupplierProduct(models.Model):
    supplier = models.ForeignKey(Supplier, related_name='products', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    supplier_sku = models.CharField(max_length=100, blank=True, null=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)


# ---------------------------
# MANUFACTURING / WORK ORDERS
# ---------------------------
class WorkOrder(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='work_orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=50, choices=[
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='draft')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} units"


# ---------------------------
# SHIPPING
# ---------------------------
class ShippingMethod(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='shipping_methods')
    name = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_days = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name} - {self.cost}"


class Shipment(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='shipments')
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE)
    shipping_method = models.ForeignKey(ShippingMethod, on_delete=models.CASCADE)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    shipped_date = models.DateField(null=True, blank=True)
    delivered_date = models.DateField(null=True, blank=True)


# ---------------------------
# REVIEWS
# ---------------------------
class ProductReview(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.product.name} - {self.rating}⭐"
