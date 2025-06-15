# # cart/models.py
# from django.db import models
# from products.models import Product
# from customer.models import Customer
# import uuid

# class Cart(models.Model):
#     customer = models.OneToOneField(Customer, on_delete=models.CASCADE)
#     session_id = models.CharField(max_length=40, unique=True, null= True, default=uuid.uuid4)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Cart for {self.customer.name}"

# from django.contrib.contenttypes.fields import GenericForeignKey
# from django.contrib.contenttypes.models import ContentType
# from django.db import models

# class CartItem(models.Model):
#     # The product can be any subclass of Product (StandardProduct, CustomProduct, ModularProduct)
#     product_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,null=True)
#     product_id = models.PositiveIntegerField(null=True)
#     product = GenericForeignKey('product_type', 'product_id')
    
#     quantity = models.PositiveIntegerField(default=1)

#     def __str__(self):
#         return f"{self.quantity} x {self.product.name} in cart"

#     def get_product(self):
#         return self.product
