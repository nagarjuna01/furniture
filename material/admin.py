from django.contrib import admin
from .models import (
    Brand, EdgeBand, Category, CategoryTypes, CategoryModel,
    WoodEn, HardwareGroup, Hardware
)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'created_at')
    search_fields = ('name',)

@admin.register(EdgeBand)
class EdgeBandAdmin(admin.ModelAdmin):
    list_display = ('id', 'edge_depth', 'e_thickness', 'brand', 'p_price', 's_price', 'sl_price')
    list_filter = ('brand',)
    search_fields = ('brand__name',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(CategoryTypes)
class CategoryTypesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)

@admin.register(CategoryModel)
class CategoryModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'model_category')
    list_filter = ('model_category',)
    search_fields = ('name',)

@admin.register(WoodEn)
class WoodEnAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'material_grp', 'material_type', 'brand',
        'length', 'width', 'thickness', 'cost_price', 'sell_price'
    )
    list_filter = ('material_grp', 'brand', 'grain')
    search_fields = ('name', 'material_type__name', 'brand__name')
    filter_horizontal = ('compatible_edgebands',)

class HardwareInline(admin.TabularInline):
    model = Hardware
    extra = 1  # Number of empty forms to display

@admin.register(HardwareGroup)
class HardwareGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    inlines = [HardwareInline]

class HardwareInline(admin.TabularInline):
    model = Hardware
    extra = 1  # Number of empty forms to display
    

@admin.register(Hardware)
class HardwareAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'h_name', 'h_group', 'brand', 'unit',
        'p_price', 's_price', 'sl_price'
    )
    list_filter = ('h_group', 'brand', 'unit')
    search_fields = ('h_name',)
    readonly_fields = ('sl_price',)

