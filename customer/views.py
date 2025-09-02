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
    

###################################################
def dashboard_view(request):
    user = request.user
    if user.user_type == 'company' and user.company:
        # Company dashboard logic
        ...
    else:
        # Freebie view logic
        ...
    
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.models import Group
from django.contrib.auth import login ,logout


User = get_user_model()
@login_required
def customer_dashboard(request):
    user = request.user
    customer = getattr(user, 'customer_profile', None)

    if customer and customer.user_type == 'company' and customer.company:
        return render(request, 'dashboards/company_dashboard.html', {'user': user})
    else:
        return render(request, 'dashboards/freebie_dashboard.html', {'user': user})

# views.py
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # For AJAX POST, or pass CSRF token in header (preferred)
def ajax_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return JsonResponse({"success": True, "redirect_url": "/dashboard/"})
            else:
                return JsonResponse({"success": False, "message": "Account is inactive."}, status=403)
        return JsonResponse({"success": False, "message": "Invalid credentials"}, status=400)
    
    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

@require_POST
@csrf_exempt
def ajax_register(request):
    username = request.POST.get("username")
    email = request.POST.get("email")
    password1 = request.POST.get("password1")
    password2 = request.POST.get("password2")

    if not all([username, email, password1, password2]):
        return JsonResponse({"success": False, "message": "All fields are required."}, status=400)

    if password1 != password2:
        return JsonResponse({"success": False, "message": "Passwords do not match."}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({"success": False, "message": "Username already taken."}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password1)

    # If you're using your custom Customer model as AbstractUser:
    user.user_type = 'freebie'
    user.save()

    # Optional group assignment
    freebie_group, _ = Group.objects.get_or_create(name="freebie")
    user.groups.add(freebie_group)

    login(request, user)
    return JsonResponse({"success": True, "redirect_url": "/dashboard/"})

@csrf_exempt
def ajax_logout(request):
    if request.method == "POST":
        logout(request)
        return JsonResponse({'success': True, 'message': 'Logged out'})
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)