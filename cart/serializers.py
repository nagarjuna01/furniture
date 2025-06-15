#  cart/serializers.py
# from rest_framework import serializers
# from .models import Cart, CartItem
# from products.serializers import ProductSerializer

# class CartItemSerializer(serializers.ModelSerializer):
#     product = ProductSerializer()

#     class Meta:
#         model = CartItem
#         fields = ['product', 'quantity']

# class CartSerializer(serializers.ModelSerializer):
#     items = CartItemSerializer(many=True)

#     class Meta:
#         model = Cart
#         fields = ['customer', 'items']
