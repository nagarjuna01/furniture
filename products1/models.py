from django.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
import uuid


class ProductType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = "Product Type"
        verbose_name_plural = "Product Types"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductSeries(models.Model):
    product_type = models.ForeignKey(
        ProductType,
        on_delete=models.CASCADE,
        related_name="series"
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)

    class Meta:
        unique_together = ("product_type", "name")
        ordering = ["name"]

    def __str__(self):
        return f"{self.product_type.name} - {self.name}"


class MeasurementUnit(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.code


class BillingUnit(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.code

class Product(models.Model):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True, editable=False)

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
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.name

    def _generate_sku(self):
        return f"PRD-{uuid.uuid4().hex[:8].upper()}"

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = self._generate_sku()
        super().save(*args, **kwargs)



class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        related_name="variants",
        on_delete=models.CASCADE
    )

    sku = models.CharField(max_length=100, unique=True)

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
        indexes = [
            models.Index(fields=["is_active"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(purchase_price__gte=0),
                name="purchase_price_positive"
            ),
            models.CheckConstraint(
                check=models.Q(selling_price__gte=0),
                name="selling_price_positive"
            ),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.sku}"

class AttributeDefinition(models.Model):
    FIELD_TYPES = (
        ("text", "Text"),
        ("number", "Number"),
        ("boolean", "Boolean"),
        ("choice", "Choice"),
    )

    name = models.CharField(max_length=100, unique=True)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    choices = models.JSONField(blank=True, default=list)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

class VariantAttributeValue(models.Model):
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
        unique_together = ("variant", "attribute")

class ProductImage(models.Model):
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
                    product=self.product
                ).update(is_primary=False)
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} Image"
class VariantImage(models.Model):
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
                    variant=self.variant
                ).update(is_primary=False)
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.variant.sku} Image"


