"""
Revinteq v3 — Tenant Middleware

IMPORTANT: Django middleware runs BEFORE DRF JWT authentication.
This means request.user is AnonymousUser here for JWT requests.

This middleware only handles SESSION-based auth (Django admin).
For JWT API requests, tenant resolution is done in TenantMixin
which runs after DRF authenticates the user.
"""
import logging
from .models import Tenant, TenantUser

logger = logging.getLogger(__name__)


class TenantMiddleware:
    """
    Sets request.tenant and request.tenant_user to None by default.
    Actual tenant resolution for JWT requests happens in TenantMixin.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Always initialise to None — DRF views will resolve via TenantMixin
        request.tenant      = None
        request.tenant_user = None
        request.is_impersonating = False

        # Session-based auth only (Django admin panel)
        if hasattr(request, 'user') and request.user.is_authenticated:
            self._resolve_tenant(request)

        return self.get_response(request)

    def _resolve_tenant(self, request):
        """Resolve tenant for session-authenticated users (Django admin)."""
        # Impersonation via session
        impersonating_id = request.session.get('impersonating_tenant_id')
        if impersonating_id:
            try:
                tenant = Tenant.objects.get(id=impersonating_id)
                request.tenant = tenant
                request.tenant_user = TenantUser(
                    user=request.user,
                    tenant=tenant,
                    role='SUPER_ADMIN',
                )
                request.is_impersonating = True
                return
            except Tenant.DoesNotExist:
                request.session.pop('impersonating_tenant_id', None)

        # Normal session user
        try:
            tu = TenantUser.objects.select_related('tenant').filter(
                user=request.user, is_active=True
            ).first()
            if tu:
                request.tenant      = tu.tenant
                request.tenant_user = tu
        except Exception:
            pass
