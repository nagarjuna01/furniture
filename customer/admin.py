from django.contrib import admin

class CustomerAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'company', 'user_type']
    list_filter = ['company', 'user_type']
