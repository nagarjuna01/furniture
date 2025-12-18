from rest_framework import viewsets, filters, permissions
from django_filters.rest_framework import DjangoFilterBackend
from .models import Client, Lead, Opportunity, SupportTicket, Interaction
from .serializers import ClientSerializer, LeadSerializer, OpportunitySerializer, SupportTicketSerializer, InteractionSerializer

# Simple permission: anyone authenticated can access. You can expand later.
class IsAuthenticatedCRM(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticatedCRM]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name', 'email', 'phone_number']
    search_fields = ['name', 'email', 'phone_number']
    ordering_fields = ['id', 'name', 'created_at']
    ordering = ['id']


class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticatedCRM]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'source']
    search_fields = ['name', 'email', 'phone_number']
    ordering_fields = ['id', 'name', 'created_at']
    ordering = ['id']


class OpportunityViewSet(viewsets.ModelViewSet):
    queryset = Opportunity.objects.all()
    serializer_class = OpportunitySerializer
    permission_classes = [IsAuthenticatedCRM]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['stage']
    search_fields = ['name']
    ordering_fields = ['id', 'name', 'expected_close_date']
    ordering = ['id']


class SupportTicketViewSet(viewsets.ModelViewSet):
    queryset = SupportTicket.objects.all()
    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticatedCRM]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority']
    search_fields = ['subject', 'client__name', 'client__email']
    ordering_fields = ['id', 'created_at']
    ordering = ['id']


class InteractionViewSet(viewsets.ModelViewSet):
    queryset = Interaction.objects.all()
    serializer_class = InteractionSerializer
    permission_classes = [IsAuthenticatedCRM]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['interaction_type', 'client']
    search_fields = ['subject', 'description', 'client__name']
    ordering_fields = ['id', 'interaction_date']
    ordering = ['interaction_date']

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def leads_page(request):
    return render(request, 'leads.html')

@login_required
def opportunities_page(request):
    return render(request, 'opportunities.html')

@login_required
def support_tickets_page(request):
    return render(request, 'support_tickets.html')

@login_required
def customers_page(request):
    return render(request, 'customers.html')

@login_required
def crm_dashboard(request):
    return render(request, 'dashboard.html')