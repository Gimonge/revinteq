from django.urls import path
from .views import (
    KommoConnectManualView, KommoConnectionStatusView,
    KommoSyncView, KommoDisconnectView, KommoFunnelView, KommoLeadsListView,
)

urlpatterns = [
    path('connect/',    KommoConnectManualView.as_view(),    name='kommo-connect'),
    path('status/',     KommoConnectionStatusView.as_view(), name='kommo-status'),
    path('sync/',       KommoSyncView.as_view(),             name='kommo-sync'),
    path('disconnect/', KommoDisconnectView.as_view(),       name='kommo-disconnect'),
    path('funnel/',     KommoFunnelView.as_view(),           name='kommo-funnel'),
    path('leads/',      KommoLeadsListView.as_view(),        name='kommo-leads'),
]
