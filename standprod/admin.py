from django.contrib import admin
from .models import (
    Tenant, TenantModule,
    ProductType, ProductModel, MeasurementUnit, BillingUnit,
    Product, ProductVariant,
    AttributeDefinition, VariantAttributeValue,
    ProductImage, VariantImage,
    ProductCategory, ProductTag, ProductCategoryAssignment, ProductTagAssignment,
    Discount, Supplier, SupplierProduct,
    WorkOrder, ShippingMethod, Shipment,
    ProductReview
)

# ---------------------------
# GENERIC TENANT FILTER MIXIN
# ---------------------------
class TenantAdminMixin:
    """Auto filter admin list by tenant if request.user has a tenant."""
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        tenant = getattr(request.user, 'tenant', None)
        if tenant is not None:
            if hasattr(qs.model, 'tenant'):
                return qs.filter(tenant=tenant)
        return qs

    def save_model(self, request, obj, form, change):
        tenant = getattr(request.user, 'tenant', None)
        if hasattr(obj, 'tenant') and tenant:
            obj.tenant = tenant
        super().save_model(request, obj, form, change)


# ---------------------------
# TENANTS
# ---------------------------
@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")


@admin.register(TenantModule)
class TenantModuleAdmin(admin.ModelAdmin):
    list_display = ("tenant", "module_name", "is_enabled")
    list_filter = ("module_name", "is_enabled")


# ---------------------------
# PRODUCT CATALOG
# ---------------------------
@admin.register(ProductType)
class ProductTypeAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "tenant")
    search_fields = ("name",)


@admin.register(ProductModel)
class ProductModelAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("name", "code", "type", "tenant")
    search_fields = ("name", "code")


@admin.register(MeasurementUnit)
class MeasurementUnitAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "symbol", "system", "base_unit", "factor", "tenant")
    search_fields = ("name", "code", "symbol")
    list_filter = ("system", "tenant")


@admin.register(BillingUnit)
class BillingUnitAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("name", "code", "tenant")


@admin.register(Product)
class ProductAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("name", "sku", "type", "model", "is_active", "tenant", "created_at")
    list_filter = ("is_active", "type")
    search_fields = ("name", "sku")


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "sku", "length", "width", "height", "selling_price", "is_active")
    search_fields = ("sku", "product__name")
    list_filter = ("is_active",)


# ---------------------------
# ATTRIBUTES
# ---------------------------
@admin.register(AttributeDefinition)
class AttributeDefinitionAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("name", "field_type", "tenant")
    list_filter = ("field_type",)
    search_fields = ("name",)


@admin.register(VariantAttributeValue)
class VariantAttributeValueAdmin(admin.ModelAdmin):
    list_display = ("variant", "attribute", "value")
    search_fields = ("variant__sku", "attribute__name")


# ---------------------------
# MEDIA
# ---------------------------
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "is_primary")
    list_filter = ("is_primary",)


@admin.register(VariantImage)
class VariantImageAdmin(admin.ModelAdmin):
    list_display = ("variant", "is_primary")
    list_filter = ("is_primary",)


# ---------------------------
# CATEGORY & TAGS
# ---------------------------
@admin.register(ProductCategory)
class ProductCategoryAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "tenant")
    search_fields = ("name",)


@admin.register(ProductTag)
class ProductTagAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("name", "tenant")
    search_fields = ("name",)


admin.site.register(ProductCategoryAssignment)
admin.site.register(ProductTagAssignment)


# ---------------------------
# DISCOUNTS
# ---------------------------
@admin.register(Discount)
class DiscountAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = (
        "name",
        "product",
        "percentage",
        "fixed_amount",
        "start_date",
        "end_date",
        "tenant",
    )
    search_fields = ("name", "product__name")
    list_filter = ("start_date", "end_date")


# ---------------------------
# SUPPLIERS
# ---------------------------
@admin.register(Supplier)
class SupplierAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("name", "contact_email", "contact_phone", "tenant")
    search_fields = ("name", "contact_email", "contact_phone")


@admin.register(SupplierProduct)
class SupplierProductAdmin(admin.ModelAdmin):
    list_display = ("supplier", "product", "supplier_sku", "purchase_price")


# ---------------------------
# WORK ORDERS
# ---------------------------
@admin.register(WorkOrder)
class WorkOrderAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("product", "quantity", "status", "start_date", "end_date", "tenant")
    list_filter = ("status",)
    search_fields = ("product__name",)


# ---------------------------
# SHIPPING
# ---------------------------
@admin.register(ShippingMethod)
class ShippingMethodAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("name", "cost", "estimated_days", "tenant")
    search_fields = ("name",)


@admin.register(Shipment)
class ShipmentAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = (
        "work_order",
        "shipping_method",
        "tracking_number",
        "shipped_date",
        "delivered_date",
        "tenant",
    )
    list_filter = ("shipped_date", "delivered_date")


# ---------------------------
# REVIEWS
# ---------------------------
@admin.register(ProductReview)
class ProductReviewAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("product", "rating", "approved", "created_at", "tenant")
    list_filter = ("approved", "rating")
    search_fields = ("product__name",)
