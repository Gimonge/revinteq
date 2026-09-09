from django.contrib import admin
from .models import KommoConnection, KommoMatchedLead


@admin.register(KommoConnection)
class KommoConnectionAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'subdomain', 'sync_enabled', 'last_synced', 'connected_at']
    list_filter  = ['sync_enabled']
    readonly_fields = ['connected_at', 'last_synced', 'token_expires_at']


@admin.register(KommoMatchedLead)
class KommoMatchedLeadAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'kommo_lead_id', 'status', 'match_method', 'match_attempts', 'won_amount']
    list_filter  = ['status', 'match_method']
    readonly_fields = ['matched_at', 'last_checked', 'created_at', 'updated_at']
