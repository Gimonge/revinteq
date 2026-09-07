from django.urls import path
from .views import DashboardMetricsView, PeriodMetricsView, AdPerformanceView
urlpatterns = [
    path('dashboard/', DashboardMetricsView.as_view(), name='metrics-dashboard'),
    path('period/',    PeriodMetricsView.as_view(),    name='metrics-period'),
    path('by-ad/',     AdPerformanceView.as_view(),    name='metrics-by-ad'),
]

# Additional endpoints used by Vue frontend
from .views import SnapshotView, DailySalesView, AdSpendSummaryView
urlpatterns += [
    path('snapshot/', SnapshotView.as_view(), name='metrics-snapshot'),
    path('daily/',    DailySalesView.as_view(), name='metrics-daily'),
    path('adspend/',   AdSpendSummaryView.as_view(), name='metrics-adspend'),
]
