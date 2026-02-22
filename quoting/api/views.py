from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProjectInitSerializer
from customer.models import Client,Lead
from ..models import QuoteRequest

class ProjectInitView(APIView):
    """
    Atomic Handshake: Ensures Client, Lead, and Quote are created 
    safely or rolled back on failure.
    """
    @transaction.atomic
    def post(self, request):
        serializer = ProjectInitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        data = serializer.validated_data
        tenant = request.user.tenant

        # INTEGRITY CHECK: Get-or-Create Client via TaxID
        client, _ = Client.objects.get_or_create(
            tenant=tenant,
            tax_id=data['client'].get('tax_id'),
            defaults={'name': data['client']['company_name']}
        )

        # CREATE CRM LEAD
        lead = Lead.objects.create(
            tenant=tenant,
            client=client,
            name=data['name'],
            email=data['email'],
            source=data['source']
        )

        # INITIALIZE QUOTE
        quote = QuoteRequest.objects.create(
            tenant=tenant,
            lead=lead,
            customer_display_name=f"Project: {data['name']}"
        )

        return Response({"id": quote.id}, status=status.HTTP_201_CREATED)
    
