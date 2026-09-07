from django.contrib import admin
from .models import Tenant, TenantUser, TenantInvitation

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display  = ['name', 'slug', 'status', 'currency', 'meta_fb_connected', 'meta_ig_connected', 'created_at']
    list_filter   = ['status', 'currency']
    search_fields = ['name', 'contact_email']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['id', 'created_at']

@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    list_display  = ['user', 'tenant', 'role', 'is_active', 'joined_at']
    list_filter   = ['role', 'is_active']
    readonly_fields = ['joined_at']

@admin.register(TenantInvitation)
class TenantInvitationAdmin(admin.ModelAdmin):
    list_display  = ['email', 'tenant', 'role', 'status', 'expires_at']
    list_filter   = ['status', 'role']
    readonly_fields = ['token', 'created_at', 'accepted_at']
