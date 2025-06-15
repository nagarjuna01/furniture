# orders/admin.py
from django.contrib import admin
from .models import Order, OrderProduct
from payment.models import Payment

class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 1  # This determines how many empty rows to display

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'status', 'total_price', 'created_at')
    list_filter = ('status',)
    search_fields = ('customer_name',)
    inlines = [OrderProductInline]

admin.site.register(Order, OrderAdmin)
admin.site.register(OrderProduct)
admin.site.register(Payment)
