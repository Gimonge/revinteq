from django.contrib import admin
from .models import MPesaConfig, MPesaTransaction

@admin.register(MPesaConfig)
class MPesaConfigAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'shortcode', 'shortcode_type', 'environment', 'is_active']
    readonly_fields = ['created_at']

@admin.register(MPesaTransaction)
class MPesaTransactionAdmin(admin.ModelAdmin):
    list_display  = ['tenant', 'transaction_id', 'amount', 'status', 'transaction_time']
    list_filter   = ['status', 'transaction_type']
    search_fields = ['transaction_id', 'bill_ref_number']
    ordering      = ['-transaction_time']
    readonly_fields = ['received_at', 'matched_at']
