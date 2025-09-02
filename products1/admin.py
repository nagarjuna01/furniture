from django.contrib import admin
from .models import *

class VariantImageInline(admin.TabularInline):
    model = VariantImage
    extra = 1

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'type', 'model', 'is_active']
    search_fields = ['name', 'sku']
    inlines = [ProductVariantInline, ProductImageInline]

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['sku', 'product', 'length', 'width', 'height']
    search_fields = ['sku']
    inlines = [VariantImageInline]

admin.site.register(ProductType)
admin.site.register(ProductModel)
admin.site.register(BillingUnit)
admin.site.register(MeasurementUnit)
admin.site.register(AttributeDefinition)
