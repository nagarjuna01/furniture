# payment/urls.py
from django.urls import path
from .views import PhonePePaymentView, PhonePeCallbackView

urlpatterns = [
    path('payment/', PhonePePaymentView.as_view(), name='phonepe-payment'),
    path('payment/callback/', PhonePeCallbackView.as_view(), name='phonepe-callback'),
]
