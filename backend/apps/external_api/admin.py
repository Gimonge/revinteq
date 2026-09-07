from django.contrib import admin
from .models import ExternalAPIKey, WebhookEndpoint, WebhookDelivery

@admin.register(ExternalAPIKey)
class ExternalAPIKeyAdmin(admin.ModelAdmin):
    list_display  = ['tenant', 'name', 'is_active', 'last_used_at', 'created_at']
    list_filter   = ['is_active']
    readonly_fields = ['key', 'created_at', 'last_used_at']

@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'url', 'is_active']

@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = ['endpoint', 'event', 'status', 'attempt_count', 'created_at']
    list_filter  = ['status', 'event']
    ordering     = ['-created_at']
