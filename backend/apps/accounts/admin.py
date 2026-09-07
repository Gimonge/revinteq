from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from apps.tenants.models import TenantUser
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False


class TenantMembershipInline(admin.TabularInline):
    model = TenantUser
    fk_name = 'user'          # TenantUser has two FKs to User — specify which one
    extra = 0
    readonly_fields = ['joined_at']
    fields = ['tenant', 'role', 'is_active', 'joined_at']


class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline, TenantMembershipInline]
    list_display  = ['email', 'first_name', 'last_name', 'is_active', 'date_joined']
    list_filter   = ['is_active', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name']


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
