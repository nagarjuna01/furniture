from django.contrib import admin
from .models import (
    QuoteRequest, 
    QuoteSolution, 
    QuoteProduct, 
    QuotePart, 
    QuotePartHardware,
    QuoteLineItem,
    OverrideLog
)
from decimal import Decimal
# 1. DNA Level Inlines
class HardwareInline(admin.TabularInline):
    model = QuotePartHardware
    extra = 0
    # Matches your model fields: quote_part, hardware, unit_sp, total_sp
    fields = ['hardware', 'quantity', 'unit_cp', 'unit_sp', 'total_sp']
    readonly_fields = ['total_sp']

class PartInline(admin.StackedInline):
    model = QuotePart
    extra = 0
    # Matches your model fields: quote_product, part_name, material, total_part_sp
    fields = ['part_name', 'material', 'part_qty', 'length_mm', 'width_mm', 'total_part_sp']
    readonly_fields = ['total_part_sp']
    show_change_link = True

# 2. Hierarchy Level Inlines
class ProductInline(admin.StackedInline):
    model = QuoteProduct
    extra = 0
    show_change_link = True
    fields = ['product_template', 'length_mm', 'width_mm', 'height_mm', 'quantity', 'total_sp', 'status']
    readonly_fields = ['total_sp']

class SolutionInline(admin.TabularInline):
    model = QuoteSolution
    extra = 0
    show_change_link = True
    fields = ['name', 'total_sp']
    readonly_fields = ['total_sp']

# 3. Model Admins
@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ['quote_number', 'customer_display_name', 'status', 'total_sp', 'revision_number']
    list_filter = ['status', 'lead_source', 'is_locked']
    search_fields = ['quote_number', 'customer_display_name']
    inlines = [SolutionInline]
    
    # These use @property or methods to avoid admin.E035
    readonly_fields = ['quote_number', 'total_sp', 'tax_amount_display', 'grand_total_display']

    def tax_amount_display(self, obj):
        # Calculation logic based on your model's tax_percentage field
        return (obj.total_sp * (obj.tax_percentage / 100)).quantize(Decimal('0.01'))
    tax_amount_display.short_description = "Tax Amount"

    def grand_total_display(self, obj):
        tax = (obj.total_sp * (obj.tax_percentage / 100))
        return (obj.total_sp + tax + obj.shipping_charges).quantize(Decimal('0.01'))
    grand_total_display.short_description = "Grand Total"

@admin.register(QuoteProduct)
class QuoteProductAdmin(admin.ModelAdmin):
    # Fixed: list_display[1] now uses 'solution' as per your models.py
    list_display = ['id', 'solution', 'product_template', 'status']
    list_filter = ['status', 'validated']
    inlines = [PartInline]

@admin.register(QuotePart)
class QuotePartAdmin(admin.ModelAdmin):
    list_display = ['part_name', 'quote_product', 'total_part_sp']
    inlines = [HardwareInline]

@admin.register(QuotePartHardware)
class QuoteHardwareAdmin(admin.ModelAdmin):
    # Fixed: uses 'quote_part' and 'hardware' as per your models.py
    list_display = ['hardware', 'quote_part', 'quantity', 'total_sp']

@admin.register(QuoteSolution)
class QuoteSolutionAdmin(admin.ModelAdmin):
    list_display = ['name', 'quote', 'total_sp']
    inlines = [ProductInline]