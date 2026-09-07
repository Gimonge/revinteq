from django.contrib import admin
from .models import SMSConfig, SMSMessage, SMSTrigger

@admin.register(SMSConfig)
class SMSConfigAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'username', 'sender_id', 'is_active', 'credit_balance']

@admin.register(SMSMessage)
class SMSMessageAdmin(admin.ModelAdmin):
    list_display  = ['tenant', 'recipient_number', 'status', 'source', 'cost', 'sent_at']
    list_filter   = ['status', 'source']
    ordering      = ['-created_at']

@admin.register(SMSTrigger)
class SMSTriggerAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'trigger', 'is_active']
    list_filter  = ['is_active']
