from django.contrib import admin
from .models import Sale

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display  = ['tenant', 'product_name', 'amount', 'payment_method', 'platform_source', 'sale_date', 'is_confirmed']
    list_filter   = ['payment_method', 'platform_source', 'is_confirmed']
    search_fields = ['product_name', 'payment_reference']
    ordering      = ['-sale_date']
    readonly_fields = ['created_at']
