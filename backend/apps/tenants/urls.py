"""Revinteq v3 — Tenants URLs"""
from django.urls import path
from .views import (
    TenantListCreateView, TenantDetailView,
    InviteClientView, AcceptInvitationView,
    ImpersonateTenantView, AdminOverviewView,
)

urlpatterns = [
    path('',                            TenantListCreateView.as_view(),  name='tenant-list'),
    path('<uuid:tenant_id>/',           TenantDetailView.as_view(),      name='tenant-detail'),
    path('<uuid:tenant_id>/invite/',    InviteClientView.as_view(),      name='tenant-invite'),
    path('accept-invite/',              AcceptInvitationView.as_view(),  name='accept-invite'),
    path('impersonate/<str:tenant_id>/', ImpersonateTenantView.as_view(), name='impersonate'),
    path('overview/',                   AdminOverviewView.as_view(),     name='admin-overview'),
]

# Extra: members list
from .views import TenantMembersView
urlpatterns += [
    path('<uuid:tenant_id>/members/', TenantMembersView.as_view(), name='tenant-members'),
]
