# # cart/views.py
# from rest_framework import viewsets
# from .models import Cart
# from .serializers import CartSerializer
# from rest_framework.permissions import IsAuthenticated

# class CartViewSet(viewsets.ModelViewSet):
#     queryset = Cart.objects.all()
#     serializer_class = CartSerializer
#     permission_classes = [IsAuthenticated]  # Only authenticated users can access their cart

# from django.shortcuts import render, get_object_or_404,redirect
# from django.http import JsonResponse
# from .models import Cart, CartItem
# from products.models import Product
# from django.contrib.auth.decorators import login_required
# from django.utils import timezone

# def get_or_create_cart(request):
#     if request.user.is_authenticated:
#         return Cart.objects.get_or_create(customer=request.user)[0]
#     else:
#         session_id = request.session.session_key or request.session.create()
#         return Cart.objects.get_or_create(session_id=session_id)[0]

# @login_required
# def cart_view(request):
#     cart = get_object_or_404(Cart, customer=request.user)
#     cart_items = CartItem.objects.filter(cart=cart)
#     total_price = sum(item.total_price for item in cart_items)
#     return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})

# @login_required
# def add_to_cart(request):
#     if request.method == 'POST':
#         product_id = request.POST.get('product_id')
#         quantity = request.POST.get('quantity', 1)
#         product = get_object_or_404(Product, id=product_id)
#         cart = get_or_create_cart(request)

#         cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
#         if not created:
#             cart_item.quantity += int(quantity)
#         else:
#             cart_item.quantity = int(quantity)

#         cart_item.save()

#         return JsonResponse({'status': 'success', 'message': 'Item added to cart'})

# @login_required
# def update_cart(request):
#     if request.method == 'POST':
#         cart_item_id = request.POST.get('cart_item_id')
#         quantity = request.POST.get('quantity')

#         cart_item = get_object_or_404(CartItem, id=cart_item_id)
#         cart_item.quantity = quantity
#         cart_item.save()

#         return JsonResponse({'status': 'success', 'message': 'Cart updated'})

# @login_required
# def remove_from_cart(request):
#     if request.method == 'POST':
#         cart_item_id = request.POST.get('cart_item_id')
#         cart_item = get_object_or_404(CartItem, id=cart_item_id)
#         cart_item.delete()

#         return JsonResponse({'status': 'success', 'message': 'Item removed from cart'})

# @login_required
# def checkout_view(request):
#     cart = get_or_create_cart(request)
#     cart_items = CartItem.objects.filter(cart=cart)
    
#     if request.method == 'POST':
#         # Here you can handle order creation
#         total_price = sum(item.total_price for item in cart_items)
#         # Create Order logic here
#         # ...

#         # Clear the cart after checkout
#         cart_items.delete()
#         return JsonResponse({'status': 'success', 'message': 'Checkout successful!'})

#     return render(request, 'checkout.html', {'cart_items': cart_items, 'total_price': total_price})

