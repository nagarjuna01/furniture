from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from rest_framework import viewsets, permissions
from .models import GlobalVariable
from .serializers import GlobalVariableSerializer
from .mixins import TenantSafeViewSetMixin
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum
from .models import Tenant
from .mixins import TenantSafeViewSetMixin
from rest_framework.views import APIView

class GlobalVariableViewSet(TenantSafeViewSetMixin, viewsets.ModelViewSet):
    serializer_class = GlobalVariableSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = GlobalVariable.objects.all()

def material_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("/material/brand/")

        return render(request, "pages/login.html", {
            "error": "Invalid credentials"
        })

    return render(request, "pages/login.html")


def material_logout(request):
    logout(request)
    return redirect("material-login")


def subscription_expired(request):
    return render(request, "pages/subscription_expired.html")

# accounts/views.py
class GlobalCommandCenterView(APIView):
    def get(self, request):
        if not request.user.is_superuser:
            return Response({"detail": "Forbidden"}, status=403)
            
        # Get data across ALL factories [cite: 4, 18]
        tenants = Tenant.objects.annotate(
            user_count=Count('users'),
            # We can link this to your Quote models later
            total_revenue=Sum('quoterequest_set__total_sp') 
        ).values('name', 'status', 'user_count', 'total_revenue')
        
        return Response(tenants)

class SuperAdminDashboardViewSet(TenantSafeViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    Global Command Center for the 15-site rollout.
    """
    queryset = Tenant.objects.all()
    permission_classes = [permissions.IsAdminUser] # Strictly Superusers

    @action(detail=False, methods=['get'])
    def global_stats(self, request):
        # Aggregate data across all 15 sites
        total_tenants = self.get_queryset().count()
        status_breakdown = self.get_queryset().values('status').annotate(count=Count('id'))
        
        return Response({
            "total_factories": total_tenants,
            "status_distribution": {s['status']: s['count'] for s in status_breakdown},
            # Note: total_revenue logic depends on your QuoteRequest relationship
        })