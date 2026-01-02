from rest_framework import serializers
from .models import Client, Lead, Opportunity, SupportTicket, Interaction

class ClientSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Client
        fields = '__all__'
        read_only_fields =('id','tenant','created_at','updated_at')


class LeadSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    client = ClientSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(), source='client', write_only=True
    )

    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields =('id','tenant','created_at','updated_at')


class OpportunitySerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    client = ClientSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(), source='client', write_only=True
    )
    lead_id = serializers.PrimaryKeyRelatedField(
        queryset=Lead.objects.all(), source='lead', write_only=True, required=False
    )

    class Meta:
        model = Opportunity
        fields = '__all__'
        read_only_fields =('id','tenant','created_at','updated_at')


class SupportTicketSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    client = ClientSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(), source='client', write_only=True
    )

    class Meta:
        model = SupportTicket
        fields = '__all__'
        read_only_fields = ("tenant", "created_at", "updated_at", "resolved_at")


class InteractionSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    client = ClientSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(), source='client', write_only=True
    )

    class Meta:
        model = Interaction
        fields = '__all__'
        read_only_fields =('id','tenant','created_at','updated_at')
