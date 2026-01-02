# orders/views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from accounts.mixins import TenantSafeViewSetMixin
from .models import Order, OrderProduct
from .serializers import OrderSerializer, OrderProductSerializer
from products.models import Product,Coupon
from django.http import JsonResponse

class OrderViewSet(TenantSafeViewSetMixin,viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated] 

    def perform_create(self, serializer):
        """
        Override perform_create to calculate the total price of the order
        before saving the order.
        """
        serializer.save(total_price=self.calculate_total_price(serializer.validated_data['products']))

    def calculate_total_price(self, products_data):
        """
        Custom method to calculate the total price of the order.
        """
        total = 0
        for product_data in products_data:
            total += product_data['quantity'] * product_data['product']['price']
        return total

    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """
        Custom action to get all products in a particular order.
        """
        order = self.get_object()
        order_products = OrderProduct.objects.filter(order=order)
        serialized_order_products = OrderProductSerializer(order_products, many=True)
        return Response(serialized_order_products.data)

class OrderHistoryView(APIView):
    def get(self, request, *args, **kwargs):
        user_orders = Order.objects.filter(customer_email=request.user.email)  # Assuming user is logged in
        order_data = [
            {
                'order_id': order.id,
                'status': order.status,
                'total_price': order.total_price,
                'created_at': order.created_at,
                'updated_at': order.updated_at
            }
            for order in user_orders
        ]
        return Response(order_data, status=status.HTTP_200_OK)

class CheckoutView(APIView):
    def post(self, request, *args, **kwargs):
        coupon_code = request.data.get('coupon_code')
        order = Order.objects.create(customer_name=request.user.name, total_price=100)  # Just an example

        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                if coupon.is_valid():
                    order.coupon = coupon
                    order.save()
                else:
                    return JsonResponse({"error": "Invalid or expired coupon"}, status=400)
            except Coupon.DoesNotExist:
                return JsonResponse({"error": "Coupon not found"}, status=400)
        
        return JsonResponse({
            "total_price": order.total_price_with_discount
        })