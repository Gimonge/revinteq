from django.urls import path
from .views import (
    ExternalSaleCreateView, ExternalSaleListView,
    ExternalPipelineCreateView, ExternalMetricsSummaryView,
    APIKeyListCreateView, APIKeyRevokeView,
)

urlpatterns = [
    # External (API key auth)
    path('v1/sales/',         ExternalSaleCreateView.as_view(),   name='ext-sale-create'),
    path('v1/sales/list/',    ExternalSaleListView.as_view(),      name='ext-sale-list'),
    path('v1/pipeline/',      ExternalPipelineCreateView.as_view(), name='ext-pipeline'),
    path('v1/metrics/',       ExternalMetricsSummaryView.as_view(), name='ext-metrics'),
    # Admin management
    path('admin/keys/<uuid:tenant_id>/',        APIKeyListCreateView.as_view(), name='api-key-list'),
    path('admin/keys/<uuid:key_id>/revoke/',    APIKeyRevokeView.as_view(),     name='api-key-revoke'),
]

# Frontend admin panel endpoints
from .views import AdminAPIKeyListView
urlpatterns += [
    path('api-keys/',             AdminAPIKeyListView.as_view(),  name='admin-api-keys'),
    path('api-keys/<uuid:key_id>/', AdminAPIKeyListView.as_view(), name='admin-api-key-detail'),
]
