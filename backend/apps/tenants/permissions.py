"""
Revinteq v3 — Tenant Permission Classes
All API views use these permission classes to enforce data isolation.
"""
from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """Only Gimsc Solutions super admins."""
    message = 'Super admin access required.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Django superuser always passes
        if request.user.is_superuser:
            return True
        return (
            hasattr(request, 'tenant_user') and
            request.tenant_user and
            request.tenant_user.role == 'SUPER_ADMIN'
        )


class IsAdminOrSuperAdmin(BasePermission):
    """Gimsc Solutions admins and super admins."""
    message = 'Admin access required.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Django superuser always passes
        if request.user.is_superuser:
            return True
        return (
            hasattr(request, 'tenant_user') and
            request.tenant_user and
            request.tenant_user.role in ('SUPER_ADMIN', 'ADMIN')
        )


class IsClientOrAdmin(BasePermission):
    """Any authenticated user with a valid tenant membership."""
    message = 'You must be logged in to a valid account.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Django superuser always passes
        if request.user.is_superuser:
            return True
        # Check middleware-attached tenant
        if (hasattr(request, 'tenant') and request.tenant is not None and
                hasattr(request, 'tenant_user') and request.tenant_user is not None):
            return True
        # Fallback: direct DB lookup in case middleware failed
        from apps.tenants.models import TenantUser
        tu = TenantUser.objects.filter(user=request.user).first()
        if tu:
            # Attach to request for downstream use
            request.tenant = tu.tenant
            request.tenant_user = tu
            return True
        return False


class IsTenantActive(BasePermission):
    """Tenant account must be active or trial."""
    message = 'Your account is suspended. Please contact Revinteq support.'

    def has_permission(self, request, view):
        if not hasattr(request, 'tenant') or not request.tenant:
            return False
        return request.tenant.status in ('active', 'trial')


class BelongsToTenant(BasePermission):
    """Object-level: the object must belong to request.tenant."""
    message = 'You do not have permission to access this resource.'

    def has_object_permission(self, request, view, obj):
        if not hasattr(request, 'tenant') or not request.tenant:
            return False
        # Support objects with either .tenant or .account.tenant
        if hasattr(obj, 'tenant'):
            return obj.tenant == request.tenant
        if hasattr(obj, 'account') and hasattr(obj.account, 'tenant'):
            return obj.account.tenant == request.tenant
        return False


def get_tenant_queryset(queryset, request):
    """
    Helper: filter any queryset to the current tenant.
    Use in every view's get_queryset() method.

    Usage:
        def get_queryset(self):
            return get_tenant_queryset(Sale.objects.all(), self.request)
    """
    if not hasattr(request, 'tenant') or not request.tenant:
        return queryset.none()
    if hasattr(queryset.model, 'tenant'):
        return queryset.filter(tenant=request.tenant)
    return queryset.none()
