from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from rest_framework import viewsets, permissions
from .models import GlobalVariable
from .serializers import GlobalVariableSerializer


class GlobalVariableViewSet(viewsets.ModelViewSet):
    serializer_class = GlobalVariableSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter variables strictly by the user's tenant
        return GlobalVariable.objects.filter(tenant=self.request.user.tenant)

    def perform_create(self, serializer):
        # Automatically assign the tenant from the authenticated user
        serializer.save(tenant=self.request.user.tenant)

def material_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("/material/brand/")  # or dashboard

        return render(request, "pages/login.html", {
            "error": "Invalid credentials"
        })

    return render(request, "pages/login.html")


def material_logout(request):
    logout(request)
    return redirect("material-login")


def subscription_expired(request):
    return render(request, "pages/subscription_expired.html")

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required(login_url="/accounts/login/")
def brand_list_page(request):
    return render(request, "brand_list.html")
