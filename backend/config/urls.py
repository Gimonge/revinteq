from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/',                   admin.site.urls),
    path('api/v1/auth/',             include('apps.accounts.urls')),
    path('api/v1/tenants/',          include('apps.tenants.urls')),
    path('api/v1/meta/',             include('apps.meta_integration.urls')),
    path('api/v1/crm/',              include('apps.crm.urls')),
    path('api/v1/whatsapp/',         include('apps.whatsapp_tracking.urls')),
    path('api/v1/sales/',            include('apps.sales.urls')),
    path('api/v1/pipeline/',         include('apps.pipeline.urls')),
    path('api/v1/metrics/',          include('apps.metrics.urls')),
    path('api/v1/revenue-goals/',    include('apps.revenue_goals.urls')),
    path('api/v1/recommendations/',  include('apps.recommendations.urls')),
    path('api/v1/mpesa/',            include('apps.mpesa.urls')),
    path('api/v1/mpesa/callback/',   include('apps.mpesa.callback_urls')),
    path('api/v1/sms/',              include('apps.sms.urls')),
    path('api/v1/bulk-upload/',      include('apps.bulk_upload.urls')),
    path('api/v1/customers/',        include('apps.customers.urls')),
    path('api/external/',            include('apps.external_api.urls')),
    path('api/schema/',              SpectacularAPIView.as_view(),                    name='schema'),
    path('api/docs/',                SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
]
