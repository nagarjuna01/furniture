# # cart/urls.py
# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import CartViewSet,cart_view, add_to_cart, update_cart, remove_from_cart,checkout_view

# router = DefaultRouter()
# router.register(r'cartapi', CartViewSet)

# urlpatterns = [
#     path('', include(router.urls)),

#     path('cart/', cart_view, name='cart_view'),
#     path('cart/add/', add_to_cart, name='add_to_cart'),
#     path('cart/update/', update_cart, name='update_cart'),
#     path('cart/remove/', remove_from_cart, name='remove_from_cart'),
#     path('cart/checkout/', checkout_view, name='checkout_view'),
# ]
