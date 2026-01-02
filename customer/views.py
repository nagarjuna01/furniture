from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Client, Lead, Opportunity, SupportTicket, Interaction
from .serializers import ClientSerializer, LeadSerializer, OpportunitySerializer, SupportTicketSerializer, InteractionSerializer
from accounts.mixins import TenantSafeViewSetMixin
# Simple permission: anyone authenticated can access. You can expand later.

class ClientViewSet(TenantSafeViewSetMixin,viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name', 'email', 'phone_number']
    search_fields = ['name', 'email', 'phone_number']
    ordering_fields = ['id', 'name', 'created_at']
    ordering = ['id']


class LeadViewSet(TenantSafeViewSetMixin,viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'source']
    search_fields = ['name', 'email', 'phone_number']
    ordering_fields = ['id', 'name', 'created_at']
    ordering = ['id']


class OpportunityViewSet(TenantSafeViewSetMixin,viewsets.ModelViewSet):
    queryset = Opportunity.objects.all()
    serializer_class = OpportunitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['stage']
    search_fields = ['name']
    ordering_fields = ['id', 'name', 'expected_close_date']
    ordering = ['id']


class SupportTicketViewSet(TenantSafeViewSetMixin,viewsets.ModelViewSet):
    queryset = SupportTicket.objects.all()
    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority']
    search_fields = ['subject', 'client__name', 'client__email']
    ordering_fields = ['id', 'created_at']
    ordering = ['id']


class InteractionViewSet(TenantSafeViewSetMixin,viewsets.ModelViewSet):
    queryset = Interaction.objects.all()
    serializer_class = InteractionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['interaction_type', 'client']
    search_fields = ['subject', 'description', 'client__name']
    ordering_fields = ['id', 'interaction_date']
    ordering = ['interaction_date']

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required(login_url="/accounts/login/")
def leads_page(request):
    return render(request, 'leads.html')

@login_required(login_url="/accounts/login/")
def opportunities_page(request):
    return render(request, 'opportunities.html')

@login_required(login_url="/accounts/login/")
def support_tickets_page(request):
    return render(request, 'support_tickets.html')

@login_required(login_url="/accounts/login/")
def customers_page(request):
    return render(request, 'customers.html')

@login_required(login_url="/accounts/login/")
def crm_dashboard(request):
    return render(request, 'dashboard.html')