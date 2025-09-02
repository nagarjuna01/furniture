from django.db import models
from django.core.exceptions import ValidationError
import datetime

class ProductType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

class ProductModel(models.Model):
    type = models.ForeignKey(ProductType, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.type.name} - {self.name}"

class MeasurementUnit(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.code

class BillingUnit(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.code



class Product(models.Model):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    type = models.ForeignKey(ProductType, null=True, blank=True, on_delete=models.SET_NULL)
    model = models.ForeignKey(ProductModel, null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
        if not self.sku:
            now = datetime.datetime.now()
            name_part = (self.name[:3] if self.name else "PRD").upper()
            type_part = (self.type.name[:2] if self.type else "TP").upper()
            model_part = (self.model.name[:2] if self.model else "BP").upper()
            timestamp = now.strftime('%m%d%M%S')
            self.sku = f"{name_part}{type_part}{model_part}{timestamp}"
        super().save(*args, **kwargs)


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
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    def clean(self):
        if Product.objects.filter(sku=self.sku).exists():
            raise ValidationError("This SKU already exists at the product level.")
    def __str__(self):
        return f"{self.product.name} ({self.length}x{self.width}x{self.height})"

class AttributeDefinition(models.Model):
    name = models.CharField(max_length=100, unique=True)
    field_type = models.CharField(max_length=20, choices=[
        ('text', 'Text'),
        ('number', 'Number'),
        ('boolean', 'Boolean'),
        ('choice', 'Choice'),
    ])
    choices = models.JSONField(blank=True, default=list)  # Used if type is 'choice'

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

    def __str__(self):
        return f"{self.product.name} Image"
    def save(self, *args, **kwargs):
        if self.is_primary:
            ProductImage.objects.filter(product=self.product).update(is_primary=False)
        super().save(*args, **kwargs)

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

