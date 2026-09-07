"""
Revinteq v3 — MetricSnapshot Model
Pre-computed KPI snapshots per tenant. Updated nightly at 03:00 EAT.
Cached in Redis (15 min TTL) for fast dashboard loads.
"""
from django.db import models
from apps.tenants.models import Tenant
import uuid


class MetricSnapshot(models.Model):
    PERIOD_CHOICES = [('day', 'Day'), ('week', 'Week'), ('month', 'Month')]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant       = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='metric_snapshots')
    period_type  = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    period_start = models.DateField()
    period_end   = models.DateField()

    # Revenue & Spend
    total_revenue    = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_spend      = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    facebook_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    facebook_spend   = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    instagram_revenue= models.DecimalField(max_digits=14, decimal_places=2, default=0)
    instagram_spend  = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # Volume
    total_conversations = models.PositiveIntegerField(default=0)
    total_sales         = models.PositiveIntegerField(default=0)
    facebook_sales      = models.PositiveIntegerField(default=0)
    instagram_sales     = models.PositiveIntegerField(default=0)
    organic_sales       = models.PositiveIntegerField(default=0)
    total_impressions   = models.PositiveIntegerField(default=0)
    total_clicks        = models.PositiveIntegerField(default=0)

    # Pipeline
    pipeline_total_deals    = models.PositiveIntegerField(default=0)
    pipeline_won_deals      = models.PositiveIntegerField(default=0)
    pipeline_lost_deals     = models.PositiveIntegerField(default=0)
    pipeline_open_value     = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    avg_deal_velocity_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    # KPIs — NULL means insufficient data, not zero
    roi                   = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    facebook_roi          = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    instagram_roi         = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    cost_per_conversation = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cost_per_sale         = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    facebook_cost_per_sale= models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    instagram_cost_per_sale=models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    conversion_rate       = models.DecimalField(max_digits=6,  decimal_places=4, null=True, blank=True)

    # AOV & Customer Value
    avg_order_value  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    facebook_aov     = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    instagram_aov    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    revenue_per_client=models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Goal GPS
    revenue_goal          = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    revenue_gap           = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    required_daily_revenue= models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    goal_status = models.CharField(max_length=20, blank=True, default='')
    goal_progress_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    is_partial   = models.BooleanField(default=False)
    computed_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = 'metric_snapshots'
        unique_together = ('tenant', 'period_type', 'period_start')
        ordering        = ['-period_start']
        indexes         = [models.Index(fields=['tenant', 'period_type', 'period_start'])]

    def __str__(self):
        return f"{self.tenant.name} | {self.period_type} | {self.period_start} | ROI: {self.roi}"
