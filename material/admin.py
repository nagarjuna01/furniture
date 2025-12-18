# from django.contrib import admin
# from .models import (
#     Brand, EdgebandName, EdgeBand, Category, CategoryTypes, CategoryModel,
#     WoodMaterial, HardwareGroup, Hardware
# )


# @admin.register(Brand)
# class BrandAdmin(admin.ModelAdmin):
#     list_display = ('id', 'name', 'description', 'created_at')
#     search_fields = ('name',)


# @admin.register(EdgebandName)
# class EdgebandNameAdmin(admin.ModelAdmin):
#     list_display = ('name', 'depth')
#     search_fields = ('name',)


# @admin.register(EdgeBand)
# class EdgeBandAdmin(admin.ModelAdmin):
#     list_display = ('edgeband_name', 'e_thickness', 'brand', 'p_price', 's_price', 'sl_price')
#     list_filter = ('edgeband_name', 'brand')
#     search_fields = ('edgeband_name__name', 'brand__name')
#     autocomplete_fields = ('edgeband_name', 'brand')


# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ('id', 'name',)
#     search_fields = ('name',)


# @admin.register(CategoryTypes)
# class CategoryTypesAdmin(admin.ModelAdmin):
#     list_display = ('id', 'name', 'category')
#     list_filter = ('category',)
#     search_fields = ('name',)


# @admin.register(CategoryModel)
# class CategoryModelAdmin(admin.ModelAdmin):
#     list_display = ('id', 'name', 'model_category')
#     list_filter = ('model_category',)
#     search_fields = ('name',)


# @admin.register(WoodMaterial)
# class WoodEnAdmin(admin.ModelAdmin):
#     list_display = (
#         'id', 'name', 'material_grp', 'material_type', 'brand',
#         'length', 'width', 'thickness', 'cost_price', 'sell_price'
#     )
#     list_filter = ('material_grp', 'brand', 'grain')
#     search_fields = ('name', 'material_type__name', 'brand__name')


# class HardwareInline(admin.TabularInline):
#     model = Hardware
#     extra = 1


# @admin.register(HardwareGroup)
# class HardwareGroupAdmin(admin.ModelAdmin):
#     list_display = ('id', 'name')
#     search_fields = ('name',)
#     inlines = [HardwareInline]


# @admin.register(Hardware)
# class HardwareAdmin(admin.ModelAdmin):
#     list_display = (
#         'id', 'h_name', 'h_group', 'brand', 'unit',
#         'p_price', 's_price', 'sl_price'
#     )
#     list_filter = ('h_group', 'brand', 'unit')
#     search_fields = ('h_name',)
#     readonly_fields = ('sl_price',)
