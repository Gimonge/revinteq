from django.contrib import admin
from .models import MetricSnapshot

@admin.register(MetricSnapshot)
class MetricSnapshotAdmin(admin.ModelAdmin):
    list_display  = ['tenant', 'period_type', 'period_start', 'total_revenue', 'roi', 'avg_order_value', 'goal_status']
    list_filter   = ['period_type', 'goal_status']
    ordering      = ['-period_start']
    readonly_fields = ['computed_at']
