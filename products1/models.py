from django.db import models
from accounts.models import TenantModel, GlobalOrTenantModel
from material.models import MeasurementUnit,BillingUnit

class ProductType(GlobalOrTenantModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField()

    class Meta:
        unique_together =("tenant","slug")
        ordering = ["name"]

    def __str__(self):
        return self.name

class ProductSeries(GlobalOrTenantModel):
    product_type = models.ForeignKey(
        ProductType,
        on_delete=models.CASCADE,
        related_name="series"
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)

    class Meta:
        unique_together =("tenant", "name")
        ordering = ["name"]

    def __str__(self):
        return f"{self.product_type.name} - {self.name}"


class Product(TenantModel):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, editable=False)

    product_type = models.ForeignKey(
        ProductType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products"
    )
    product_series = models.ForeignKey(
        ProductSeries,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tenant", "name","sku")
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class ProductVariant(TenantModel):
    
    product = models.ForeignKey(
        Product,
        related_name="variants",
        on_delete=models.CASCADE
    )

    sku = models.CharField(max_length=100, editable=False)

    length = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    width = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    measurement_unit = models.ForeignKey(
        MeasurementUnit,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)

    billing_unit = models.ForeignKey(
        BillingUnit,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("tenant","sku")
        ordering = ["id"]

    def __str__(self):
        return f"{self.product.name} - {self.sku}"

class AttributeDefinition(GlobalOrTenantModel):
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
        ordering = ["name"]
        unique_together = ("tenant", "name")
    def __str__(self):
        return self.name
class VariantAttributeValue(TenantModel):
    variant = models.ForeignKey(
        ProductVariant,
        related_name="attributes",
        on_delete=models.CASCADE
    )
    attribute = models.ForeignKey(
        AttributeDefinition,
        on_delete=models.CASCADE
    )

    value = models.CharField(max_length=255)
    class Meta:
        unique_together = ("tenant", "variant", "attribute")
    def __str__(self):
        return f"{self.variant.sku} - {self.attribute.name}"

from django.db import transaction

class ProductImage(TenantModel):
    product = models.ForeignKey(
        Product,
        related_name="images",
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="products/")
    is_primary = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.is_primary:
                ProductImage.objects.filter(
                    product=self.product,
                    tenant=self.tenant
                ).update(is_primary=False)
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} Image"

class VariantImage(TenantModel):
    
    variant = models.ForeignKey(
        ProductVariant,
        related_name="images",
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="variants/")
    is_primary = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.is_primary:
                VariantImage.objects.filter(
                    variant=self.variant,
                    tenant=self.tenant
                ).update(is_primary=False)
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.variant.sku} Image"
