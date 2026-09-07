from django.urls import path
from .views import (
    AdminAdAccountView, ActiveCampaignsView, AdminAllCampaignsView,
    MetaConnectView, MetaCallbackView, AdAccountListView,
    MetaSyncView, CampaignListView, CampaignDetailView,
    MetaAuthView, AdPerformanceView,
    MetaTokenStatusView, MetaAccountSelectionView,
)

urlpatterns = [
    path('connect/',              MetaConnectView.as_view(),    name='meta-connect'),
    path('auth/',                 MetaAuthView.as_view(),       name='meta-auth'),
    path('callback/',             MetaCallbackView.as_view(),   name='meta-callback'),
    path('accounts/',             AdAccountListView.as_view(),  name='meta-accounts'),
    path('sync/',                 MetaSyncView.as_view(),       name='meta-sync'),
    path('campaigns/',            CampaignListView.as_view(),   name='meta-campaigns'),
    path('campaigns/<uuid:campaign_id>/', CampaignDetailView.as_view(), name='meta-campaign-detail'),
    path('ads/performance/',      AdPerformanceView.as_view(),       name='meta-ads-performance'),
    path('token-status/',          MetaTokenStatusView.as_view(),      name='meta-token-status'),
    path('select-account/',        MetaAccountSelectionView.as_view(), name='meta-select-account'),
    path('active-campaigns/',      ActiveCampaignsView.as_view(),      name='meta-active-campaigns'),
    path('admin/accounts/',        AdminAdAccountView.as_view(),       name='meta-admin-accounts'),
    path('admin/accounts/<uuid:account_id>/assign/', AdminAdAccountView.as_view(), name='meta-admin-assign'),
    path('admin/campaigns/',         AdminAllCampaignsView.as_view(),    name='meta-admin-campaigns'),
]
