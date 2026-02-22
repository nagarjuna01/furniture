from rest_framework import serializers
from .models import Client, Lead, Opportunity, SupportTicket, Interaction,Marketplace,MarketplaceCustomer

class ClientSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Client
        fields = '__all__'
        read_only_fields =('id','tenant','created_at','updated_at')

class MarketplaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marketplace
        fields = "__all__"
        read_only_fields = ("tenant",)


class MarketplaceCustomerSerializer(serializers.ModelSerializer):
    marketplace_name = serializers.CharField(
        source="marketplace.name", read_only=True
    )

    class Meta:
        model = MarketplaceCustomer
        fields = "__all__"
        read_only_fields = ("tenant",)

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
    marketplace_customer_name = serializers.CharField(
        source="marketplace_customer.display_name", read_only=True
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
    marketplace_customer_name = serializers.CharField(
        source="marketplace_customer.display_name", read_only=True
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
    target_name = serializers.SerializerMethodField()
    class Meta:
        model = Interaction
        fields = '__all__'
        read_only_fields =('id','tenant','created_at','updated_at')
    def get_target_name(self, obj):
        if obj.client:
            return obj.client.name
        if obj.marketplace_customer:
            return obj.marketplace_customer.display_name
        return None
