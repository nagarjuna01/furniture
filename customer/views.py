# orders/views.py or customers/views.py
from rest_framework import viewsets
from .models import Customer
from .serializers import CustomerSerializer
from django.shortcuts import render
from django.views import View

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

class CustomerRegisterView(View):
    def get(self, request):
        return render(request, 'customer_register.html')
    
