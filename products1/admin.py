from django.contrib import admin
from .models import (
    Product,
    ProductType,
    ProductSeries,
    ProductVariant,
    ProductImage,
    VariantImage,
    BillingUnit,
    MeasurementUnit,
    AttributeDefinition,
    VariantAttributeValue,
)


class VariantImageInline(admin.TabularInline):
    model = VariantImage
    extra = 1


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class VariantAttributeInline(admin.TabularInline):
    model = VariantAttributeValue
    extra = 1

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    show_change_link = True


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "product_type",
        "product_series",
        "is_active",
        "created_at",
    )
    list_filter = ("product_type", "is_active")
    search_fields = ("name", "sku")
    readonly_fields = ("sku", "created_at")
    inlines = [ProductVariantInline, ProductImageInline]

    ordering = ("-created_at",)

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "product",
        "purchase_price",
        "selling_price",
        "is_active",
    )
    list_filter = ("is_active", "product")
    search_fields = ("sku",)
    readonly_fields = ("sku",)

    inlines = [VariantAttributeInline, VariantImageInline]

@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

@admin.register(ProductSeries)
class ProductSeriesAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "product_type")
    list_filter = ("product_type",)
    search_fields = ("name", "code")

@admin.register(MeasurementUnit)
class MeasurementUnitAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")

@admin.register(AttributeDefinition)
class AttributeDefinitionAdmin(admin.ModelAdmin):
    list_display = ("name", "field_type")
    list_filter = ("field_type",)
    search_fields = ("name",)
