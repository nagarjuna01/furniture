# quotes/serializers.py
from rest_framework import serializers
from decimal import Decimal
from .models import (
    QuoteRequest, QuoteProduct, QuoteSolution, QuotePart, QuotePartHardware,OverrideLog,QuoteRevision,QuoteCommunication
)
from customer.serializers import ClientSerializer
from quoting.services.recalculation import (
    recalc_quote_product,
    recalc_quote_solution,
    recalc_quote,
)
from products1.models import Product,ProductVariant
from modular_calc.models import ModularProduct
from customer.models import Client
from material.models.wood import WoodMaterial
from modular_calc.evaluation.part_evaluator import PartEvaluator

# -----------------------------
# 1. HARDWARE & PARTS (BOM Layer)
# -----------------------------
class QuotePartHardwareSerializer(serializers.ModelSerializer):
    hardware_name = serializers.CharField(source="hardware.name", read_only=True)

    class Meta:
        model = QuotePartHardware
        fields = ["id", "hardware", "hardware_name", "quantity", "unit_sp", "total_sp"]

class QuotePartSerializer(serializers.ModelSerializer):
    hardware = QuotePartHardwareSerializer(many=True, read_only=True)
    description = serializers.SerializerMethodField()

    class Meta:
        model = QuotePart
        fields = [
            "id", "part_name", "length_mm", "width_mm", "thickness_mm", 
            "part_qty", "total_part_sp", "hardware", "description"
        ]

    def get_description(self, obj):
        return {
            "dim": f"{obj.length_mm}x{obj.width_mm}x{obj.thickness_mm}",
            "mat": obj.material.name if obj.material else "N/A"
        }

# -----------------------------
# 2. PRODUCTS (Configurator Layer)
# -----------------------------
class QuoteProductSerializer(serializers.ModelSerializer):
    parts = QuotePartSerializer(many=True, read_only=True)
    product_name = serializers.CharField(source="product_template.name", read_only=True)
    
    # Handshake IDs - Explicitly optional to allow branching
    product_template = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), required=False, allow_null=True
    )
    product_variant = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(), required=False, allow_null=True
    )
    modular_product = serializers.PrimaryKeyRelatedField(
        queryset=ModularProduct.objects.all(), required=False, allow_null=True
    )

    # Alpine.js Aliases
    l = serializers.DecimalField(source='length_mm', max_digits=12, decimal_places=2)
    w = serializers.DecimalField(source='width_mm', max_digits=12, decimal_places=2)
    h = serializers.DecimalField(source='height_mm', max_digits=12, decimal_places=2)
    is_modular = serializers.BooleanField(read_only=True)
    unit_cp = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    unit_sp = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    class Meta:
        model = QuoteProduct
        fields = [
            "id", "solution", "product_name", "product_template", 
            "product_variant", "modular_product", "l", "w", "h", "is_modular",
            "quantity","unit_cp", "unit_sp", "total_sp", "status", "parts", "config_parameters"
        ]
        read_only_fields = ["total_sp", "status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Data Integrity: Scope querysets to the tenant to fix "Invalid PK"
        request = self.context.get('request')
        if request and hasattr(request.user, 'tenant'):
            t = request.user.tenant
            self.fields['product_template'].queryset = Product.objects.filter(tenant=t)
            self.fields['product_variant'].queryset = ProductVariant.objects.filter(product__tenant=t)
            # Add modular check if the model exists
            from modular_calc.models import ModularProduct
            self.fields['modular_product'].queryset = ModularProduct.objects.filter(tenant=t)

# -----------------------------
# 3. SOLUTIONS (Zone/Room Layer)
# -----------------------------
class QuoteSolutionSerializer(serializers.ModelSerializer):
    items = QuoteProductSerializer(many=True, read_only=True, source='products')

    class Meta:
        model = QuoteSolution
        fields = ["id", "name", "items", "total_sp", "notes"]

# -----------------------------
# 4. MASTER QUOTE (Handshake Layer)
# -----------------------------
class QuoteWorkspaceSerializer(serializers.ModelSerializer):
    """The Primary Handshake Object for ProjectInitView"""
    solutions = QuoteSolutionSerializer(many=True, read_only=True)
    client_detail = ClientSerializer(source='client', read_only=True)
    tax_amount = serializers.SerializerMethodField()
    grand_total = serializers.SerializerMethodField()

    class Meta:
        model = QuoteRequest
        fields = [
            "id", "quote_number", "client_detail", "status", 
            "solutions", "total_sp", "tax_percentage", 
            "tax_amount", "grand_total", "is_locked"
        ]

    def get_tax_amount(self, obj):
        return (obj.total_sp * (obj.tax_percentage / Decimal("100"))).quantize(Decimal("1.00"))

    def get_grand_total(self, obj):
        return obj.total_sp + self.get_tax_amount(obj) + (obj.shipping_charges or Decimal("0.00"))

class QuoteRequestSerializer(serializers.ModelSerializer):
    """Simple serializer for List views and basic CRUD"""
    client_name = serializers.CharField(source='client.name', read_only=True)

    class Meta:
        model = QuoteRequest
        fields = [
            "id", "quote_number", "client", "client_name", 
            "status", "total_sp", "created_at"
        ]

class OverrideLogSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source="changed_by.get_full_name", read_only=True)

    class Meta:
        model = OverrideLog
        fields = [
            "id", "target_type", "target_id", "field_name", 
            "old_value", "new_value", "reason", "changed_by_name", "created_at"
        ]
        read_only_fields = ["changed_by", "created_at"]

class QuoteRevisionSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)

    class Meta:
        model = QuoteRevision
        fields = [
            "id", "revision_no", "snapshot", "created_at", "created_by_name"
        ]
        read_only_fields = ["revision_no", "snapshot", "created_at"]

class QuoteCommunicationSerializer(serializers.ModelSerializer):
    sent_by_name = serializers.CharField(source="sent_by.get_full_name", read_only=True)

    class Meta:
        model = QuoteCommunication
        fields = [
            "id", "quote", "channel", "recipient", 
            "sent_by", "sent_by_name", "sent_at", 
            "success", "error_message"
        ]
        read_only_fields = ["sent_by", "sent_at", "success", "error_message"]



class MarketplaceQuoteSerializer(serializers.ModelSerializer):
    """Public catalog representation of a modular product"""
    template_name = serializers.CharField(source="product_template.name", read_only=True)
    category = serializers.CharField(source="product_template.category.name", read_only=True)
    
    class Meta:
        model = QuoteProduct
        fields = ["id", "template_name", "category", "length_mm", "width_mm", "height_mm", "total_sp"]