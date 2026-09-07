from django.contrib import admin
from .models import AdAccount, Campaign, Ad, AdSpendRecord

@admin.register(AdAccount)
class AdAccountAdmin(admin.ModelAdmin):
    list_display = ['account_name', 'tenant', 'platform', 'last_synced', 'sync_enabled']
    list_filter  = ['platform', 'sync_enabled']
    readonly_fields = ['last_synced', 'token_expires_at']

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'ad_account', 'platform', 'status', 'daily_budget']
    list_filter  = ['platform', 'status']

@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = ['name', 'campaign', 'ad_format', 'status']

@admin.register(AdSpendRecord)
class AdSpendRecordAdmin(admin.ModelAdmin):
    list_display = ['ad', 'date', 'spend', 'impressions', 'clicks', 'dm_conversations']
    ordering     = ['-date']
