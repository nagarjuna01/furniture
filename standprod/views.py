# standprod/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

# ----------------------------------------
# AJAX LOGIN (Modal)
# ----------------------------------------
@csrf_exempt
def material_login(request):
    """
    AJAX ONLY — login modal posts here.
    Returns JSON instead of redirecting.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    username = request.POST.get("username")
    password = request.POST.get("password")

    if not username or not password:
        return JsonResponse({"error": "Missing credentials"}, status=400)

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse({"error": "Invalid username or password"}, status=401)

    # Login success
    login(request, user)
    return JsonResponse({"success": True, "redirect": reverse("master-admin")})


# ----------------------------------------
# LOGOUT
# ----------------------------------------
def material_logout(request):
    """
    Logout user and redirect to master admin.
    Supports AJAX if needed.
    """
    logout(request)
    
    # Check if AJAX request (modern Django)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": True, "redirect": reverse("master-admin")})
    
    return redirect("master-admin")


# ----------------------------------------
# SUBSCRIPTION EXPIRED
# ----------------------------------------
def subscription_expired(request):
    return render(request, "subscription_expired.html")


# ----------------------------------------
# MASTER ADMIN (Landing Page)
# ----------------------------------------
def master_admin(request):
    """
    Always render master admin.
    If user not authenticated → login modal auto-shows (handled in JS)
    """
    tabs = [
        {'tab': 'products', 'label': 'Products'},
        {'tab': 'types', 'label': 'Product Types'},
        {'tab': 'models', 'label': 'Product Models'},
        {'tab': 'units', 'label': 'Units'},
        {'tab': 'attributes', 'label': 'Attributes'},
        {'tab': 'discounts', 'label': 'Discounts'},
        {'tab': 'suppliers', 'label': 'Suppliers'},
        {'tab': 'workorders', 'label': 'Work Orders'},
        {'tab': 'shipping', 'label': 'Shipping'},
        {'tab': 'reviews', 'label': 'Reviews'},
    ]
    tabs_without_add = ['units', 'workorders', 'shipping', 'reviews']
    return render(
        request, 
        "master_admin.html", 
        {"tabs": tabs, "tabs_without_add": tabs_without_add}
    )



# ----------------------------------------
# DRF API: Unit Conversion
# ----------------------------------------
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import MeasurementUnit
from rest_framework.permissions import AllowAny  # adjust as needed

class ConvertAPIView(APIView):
    """
    Convert value from one measurement unit to another.
    Example: /api/convert/?from=kg&to=g&value=5
    """
    permission_classes = [AllowAny]  # Change to IsAuthenticated if needed

    def get(self, request):
        src = request.query_params.get('from')
        dst = request.query_params.get('to')
        value = request.query_params.get('value')

        if not (src and dst and value):
            return Response(
                {"detail": "from, to and value are required query params."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            val = float(value)
        except ValueError:
            return Response({"detail": "value must be numeric."}, status=status.HTTP_400_BAD_REQUEST)

        src_unit = MeasurementUnit.objects.filter(code__iexact=src).first()
        dst_unit = MeasurementUnit.objects.filter(code__iexact=dst).first()

        if not src_unit or not dst_unit:
            return Response({"detail": "Unit code not found."}, status=status.HTTP_404_NOT_FOUND)

        if src_unit.category != dst_unit.category:
            return Response({
                "detail": "Units belong to different categories and cannot be converted."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Conversion via base unit
        base_value = src_unit.convert_to_base(val)
        converted = dst_unit.convert_from_base(base_value)

        return Response({
            "from": src_unit.code,
            "to": dst_unit.code,
            "value": val,
            "converted": converted,
            "base_unit": src_unit.base_unit,
            "category": src_unit.category
        })
