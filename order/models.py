from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from accounts.models.base import TenantModel
from products.models import Coupon

class Order(TenantModel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
    ]

    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()

    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    coupon = models.ForeignKey(
        Coupon,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "status"]),
        ]

    def __str__(self):
        return f"Order #{self.pk} - {self.customer_name}"

    @property
    def total_price_with_discount(self):
        if self.coupon and self.coupon.is_valid():
            discount = (self.total_price * self.coupon.discount_percentage) / 100
            return self.total_price - discount
        return self.total_price
class OrderProduct(TenantModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField()
    product = GenericForeignKey("content_type", "object_id")

    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = (
            "tenant",
            "order",
            "content_type",
            "object_id",
        )
        indexes = [
            models.Index(fields=["tenant", "content_type", "object_id"]),
        ]

    def __str__(self):
        product_name = getattr(self.product, "name", "Unknown")
        return f"Order #{self.order_id} - {product_name}"
    def save(self, *args, **kwargs):
        if self.order and self.tenant != self.order.tenant:
            raise ValueError("OrderProduct tenant must match Order tenant")
        super().save(*args, **kwargs)
