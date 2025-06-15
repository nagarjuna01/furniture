# orders/serializers.py
from rest_framework import serializers
from .models import Order, OrderProduct
from products.models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price']
        ref_name = 'OrderProductProduct'  # Unique ref_name for this serializer to avoid conflicts

class OrderProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = OrderProduct
        fields = ['product', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    products = OrderProductSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'customer_name', 'customer_email', 'total_price', 'status', 'created_at', 'updated_at', 'products']
