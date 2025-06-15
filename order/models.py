from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from products.models import Coupon

class Order(models.Model):
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('shipped', 'Shipped'), ('delivered', 'Delivered')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"
    
    @property
    def total_price_with_discount(self):
        if self.coupon and self.coupon.is_valid():
            return self.total_price - (self.total_price * self.coupon.discount_percentage / 100)
        return self.total_price



class OrderProduct(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    content_typ = models.ForeignKey(ContentType, on_delete=models.CASCADE, null= True)
    object_id = models.PositiveIntegerField(null=True)
    product = GenericForeignKey('content_typ', 'object_id')
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('order', 'content_typ', 'object_id')

    def __str__(self):
        return f"OrderProduct for Order #{self.order.id} - Product: {self.product.name}"