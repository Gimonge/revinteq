# No views in common app — shared utilities only
"""Revinteq v3 — Common view utilities"""
from apps.tenants.models import TenantUser


def get_tenant(request):
    """
    Get the tenant for a request, with fallback to direct DB lookup.

    Priority order:
      1. X-Impersonate-Tenant header  (admin acting as a client)
      2. Middleware-attached tenant   (normal client JWT request)
      3. Direct DB lookup fallback    (superuser without a tenant)
    """
    from apps.tenants.models import Tenant

    # 1. Admin impersonation via header — highest priority
    # The frontend sets X-Impersonate-Tenant: <tenant_id> when admin
    # clicks "View as client". Superusers are allowed to impersonate.
    impersonate_id = request.headers.get('X-Impersonate-Tenant')
    if impersonate_id and request.user and request.user.is_authenticated:
        if request.user.is_superuser or getattr(request.user, 'is_staff', False):
            try:
                tenant = Tenant.objects.get(id=impersonate_id)
                request.tenant = tenant
                request.is_impersonating = True
                return tenant
            except (Tenant.DoesNotExist, Exception):
                pass

    # 2. Try middleware-attached tenant first
    tenant = getattr(request, 'tenant', None)
    if tenant:
        return tenant

    # 3. Fallback: look up directly — handles cases where middleware failed
    if request.user and request.user.is_authenticated:
        tu = TenantUser.objects.select_related('tenant').filter(
            user=request.user
        ).first()
        if tu:
            request.tenant = tu.tenant
            request.tenant_user = tu
            return tu.tenant

    return None
