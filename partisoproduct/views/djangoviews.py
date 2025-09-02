from django.shortcuts import render
from partisoproduct.models import Modular1
import requests

def modular_products_list(request):
    products = Modular1.objects.all()
    return render(request, 'new_mod1107.html', {'products': products})
def create_quote_page(request):
    return render(request, 'partisoproduct/create_quote.html')
