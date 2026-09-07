"""Revinteq v3 — re-exports from tenants.permissions for backward compatibility."""
from apps.tenants.permissions import (
    IsSuperAdmin, IsAdminOrSuperAdmin, IsClientOrAdmin,
    IsTenantActive, BelongsToTenant, get_tenant_queryset,
)
__all__ = [
    'IsSuperAdmin', 'IsAdminOrSuperAdmin', 'IsClientOrAdmin',
    'IsTenantActive', 'BelongsToTenant', 'get_tenant_queryset',
]
