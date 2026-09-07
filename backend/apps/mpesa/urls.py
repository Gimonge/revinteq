from django.urls import path
from .views import (
    MPesaTransactionListView, MPesaManualMatchView,
    MPesaConfigView, MPesaConfigTenantView,
)

urlpatterns = [
    path('transactions/',                               MPesaTransactionListView.as_view(), name='mpesa-transactions'),
    path('transactions/<uuid:transaction_id>/match/',   MPesaManualMatchView.as_view(),     name='mpesa-match'),
    path('config/',                                     MPesaConfigTenantView.as_view(),    name='mpesa-config'),
    path('admin/config/<uuid:tenant_id>/',              MPesaConfigView.as_view(),          name='mpesa-admin-config'),
]
