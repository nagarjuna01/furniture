# orders/urls.py or customers/urls.py
# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import CustomerViewSet,CustomerRegisterView

# router = DefaultRouter()
# router.register(r'customers', CustomerViewSet)

# urlpatterns = [
#     path('register/', CustomerRegisterView.as_view(), name='customer_register'),
#     path('', include(router.urls)),
# ]
from django.urls import path
from customer.views import customer_dashboard, ajax_register, ajax_login, ajax_logout
from django.shortcuts import render,redirect

from django.contrib.auth.decorators import login_required

def redirect_if_authenticated(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('customer_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

urlpatterns = [
    path('dashboard/', customer_dashboard, name='customer_dashboard'),
    
    # Registration
    path('register/', lambda r: render(r, 'registration/register.html'), name='register'),
    path('ajax-register/', ajax_register, name='ajax_register'),

    # Login
    path('login/', lambda r: render(r, 'registration/login.html'), name='login'), 
    path('ajax-login/', ajax_login, name='ajax_login'),
    path('ajax-logout/', ajax_logout, name='ajax_logout'),
]

