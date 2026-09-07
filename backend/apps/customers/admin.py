from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display  = ['name', 'tenant', 'phone_number', 'source_platform', 'total_purchases', 'total_spend', 'sms_opt_in', 'first_seen_date']
    list_filter   = ['source_platform', 'sms_opt_in', 'email_opt_in']
    search_fields = ['name', 'phone_number', 'email']
    readonly_fields = ['first_seen_date', 'total_purchases', 'total_spend', 'created_at']
    ordering      = ['-created_at']
