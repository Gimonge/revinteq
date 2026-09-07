from django.urls import path
from .views import (
    CRMLoginView, CRMRefreshView, CRMMeView,
    CRMDashboardView, CRMLeadListView, CRMLeadDetailView,
    CRMActivityView, CRMContactListView, CRMUserListView,
    CRMCustomerListView, CRMInvoiceListView, CRMInvoiceDetailView,
    CRMReceiptView, CRMFinancialSummaryView,
    CRMGooglePlacesSearchView, CRMImportLeadsView,
)

urlpatterns = [
    path("auth/login/",         CRMLoginView.as_view(),            name="crm-login"),
    path("auth/refresh/",       CRMRefreshView.as_view(),          name="crm-refresh"),
    path("auth/me/",            CRMMeView.as_view(),               name="crm-me"),
    path("dashboard/",          CRMDashboardView.as_view(),        name="crm-dashboard"),
    path("leads/",              CRMLeadListView.as_view(),         name="crm-leads"),
    path("leads/import/google/",CRMGooglePlacesSearchView.as_view(), name="crm-google-places"),
    path("leads/import/",       CRMImportLeadsView.as_view(),      name="crm-import-leads"),
    path("leads/<uuid:lead_id>/",                                  CRMLeadDetailView.as_view(),  name="crm-lead-detail"),
    path("leads/<uuid:lead_id>/activities/",                       CRMActivityView.as_view(),    name="crm-activities"),
    path("leads/<uuid:lead_id>/activities/<uuid:activity_id>/",    CRMActivityView.as_view(),    name="crm-activity-detail"),
    path("contacts/",           CRMContactListView.as_view(),      name="crm-contacts"),
    path("users/",              CRMUserListView.as_view(),         name="crm-users"),
    path("customers/",          CRMCustomerListView.as_view(),     name="crm-customers"),
    path("invoices/",           CRMInvoiceListView.as_view(),      name="crm-invoices"),
    path("invoices/<uuid:invoice_id>/",          CRMInvoiceDetailView.as_view(), name="crm-invoice-detail"),
    path("invoices/<uuid:invoice_id>/receipts/", CRMReceiptView.as_view(),       name="crm-receipts"),
    path("financial/summary/",  CRMFinancialSummaryView.as_view(), name="crm-financial-summary"),
]
