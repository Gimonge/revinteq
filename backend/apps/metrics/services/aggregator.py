"""
Revinteq v3 — Metrics Aggregator
Computes all KPIs for one tenant over a period and upserts MetricSnapshot.
"""
import logging
from datetime import date, timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Q
from apps.tenants.models import Tenant
from apps.sales.models import Sale
from apps.pipeline.models import PipelineDeal
from apps.meta_integration.models import AdSpendRecord
from apps.metrics.models import MetricSnapshot
from apps.metrics.engine import (
    compute_roi, compute_cost_per_conversion, compute_cost_per_sale,
    compute_conversion_rate, compute_aov, compute_revenue_per_client,
    compute_revenue_gap, compute_required_daily_revenue,
    compute_goal_progress, determine_goal_status,
)

logger = logging.getLogger(__name__)


class MetricsAggregator:
    def __init__(self, tenant: Tenant):
        self.tenant = tenant

    def compute_and_store(self, period_type: str, period_start: date, period_end: date):
        is_partial = period_end >= date.today()

        # ── Sales ─────────────────────────────────────────────
        sales_qs  = Sale.objects.filter(
            tenant=self.tenant,
            sale_date__range=(period_start, period_end),
            is_confirmed=True,
        )
        agg = sales_qs.aggregate(
            total_revenue     = Sum('amount'),
            total_sales       = Count('id'),
            fb_revenue        = Sum('amount', filter=Q(platform_source='facebook')),
            ig_revenue        = Sum('amount', filter=Q(platform_source='instagram')),
            fb_sales          = Count('id',   filter=Q(platform_source='facebook')),
            ig_sales          = Count('id',   filter=Q(platform_source='instagram')),
            organic_sales     = Count('id',   filter=Q(platform_source='organic')),
        )
        total_revenue     = agg['total_revenue']    or Decimal('0')
        total_sales       = agg['total_sales']      or 0
        facebook_revenue  = agg['fb_revenue']       or Decimal('0')
        instagram_revenue = agg['ig_revenue']       or Decimal('0')
        facebook_sales    = agg['fb_sales']         or 0
        instagram_sales   = agg['ig_sales']         or 0
        organic_sales     = agg['organic_sales']    or 0
        unique_clients    = total_sales  # conservative proxy

        # ── Ad Spend ──────────────────────────────────────────
        spend_qs = AdSpendRecord.objects.filter(
            ad__campaign__ad_account__tenant=self.tenant,
            date__range=(period_start, period_end),
        )
        spend_agg = spend_qs.aggregate(
            total_spend      = Sum('spend'),
            fb_spend         = Sum('spend',       filter=Q(ad__campaign__platform__in=['facebook','both'])),
            ig_spend         = Sum('spend',       filter=Q(ad__campaign__platform__in=['instagram','both'])),
            impressions      = Sum('impressions'),
            clicks           = Sum('clicks'),
            dm_conversations = Sum('dm_conversations'),
        )
        total_spend       = spend_agg['total_spend']      or Decimal('0')
        facebook_spend    = spend_agg['fb_spend']         or Decimal('0')
        instagram_spend   = spend_agg['ig_spend']         or Decimal('0')
        total_impressions = spend_agg['impressions']      or 0
        total_clicks      = spend_agg['clicks']           or 0
        total_convs       = spend_agg['dm_conversations'] or 0

        # ── Pipeline ──────────────────────────────────────────
        pipe_qs = PipelineDeal.objects.filter(
            tenant=self.tenant,
            created_at__date__range=(period_start, period_end),
        )
        won_qs  = pipe_qs.filter(stage='won')
        open_val= pipe_qs.filter(
            stage__in=['new_click','contacted','interested','negotiating']
        ).aggregate(v=Sum('estimated_value'))['v'] or Decimal('0')

        avg_vel = None
        timed   = won_qs.exclude(new_click_at=None).exclude(won_at=None)
        if timed.exists():
            total_h = sum((d.won_at - d.new_click_at).total_seconds() / 3600 for d in timed)
            avg_vel = Decimal(str(round(total_h / timed.count(), 2)))

        # ── KPIs ──────────────────────────────────────────────
        # Goal GPS
        revenue_goal = required_daily = revenue_gap = None
        goal_status  = ''
        goal_progress= None
        try:
            from apps.revenue_goals.models import RevenueGoal
            goal_obj = RevenueGoal.objects.get(
                tenant=self.tenant, month=period_start.replace(day=1)
            )
            revenue_goal  = goal_obj.target_amount
            revenue_gap   = compute_revenue_gap(revenue_goal, total_revenue)
            days_in_month = 30  # approximate
            days_remaining= max(0, (period_end - date.today()).days + 1)
            required_daily = compute_required_daily_revenue(revenue_gap, days_remaining)
            goal_status   = determine_goal_status(total_revenue, revenue_goal, days_remaining, days_in_month)
            goal_progress = compute_goal_progress(total_revenue, revenue_goal)
        except Exception:
            pass

        snapshot, _ = MetricSnapshot.objects.update_or_create(
            tenant=self.tenant, period_type=period_type, period_start=period_start,
            defaults={
                'period_end':              period_end,
                'total_revenue':           total_revenue,
                'total_spend':             total_spend,
                'facebook_revenue':        facebook_revenue,
                'facebook_spend':          facebook_spend,
                'instagram_revenue':       instagram_revenue,
                'instagram_spend':         instagram_spend,
                'total_conversations':     total_convs,
                'total_sales':             total_sales,
                'facebook_sales':          facebook_sales,
                'instagram_sales':         instagram_sales,
                'organic_sales':           organic_sales,
                'total_impressions':       total_impressions,
                'total_clicks':            total_clicks,
                'pipeline_total_deals':    pipe_qs.count(),
                'pipeline_won_deals':      won_qs.count(),
                'pipeline_lost_deals':     pipe_qs.filter(stage='lost').count(),
                'pipeline_open_value':     open_val,
                'avg_deal_velocity_hours': avg_vel,
                'roi':                     compute_roi(total_revenue, total_spend),
                'facebook_roi':            compute_roi(facebook_revenue, facebook_spend),
                'instagram_roi':           compute_roi(instagram_revenue, instagram_spend),
                'cost_per_conversation':   compute_cost_per_conversion(total_spend, total_convs),
                'cost_per_sale':           compute_cost_per_sale(total_spend, total_sales),
                'facebook_cost_per_sale':  compute_cost_per_sale(facebook_spend, facebook_sales),
                'instagram_cost_per_sale': compute_cost_per_sale(instagram_spend, instagram_sales),
                'conversion_rate':         compute_conversion_rate(total_sales, total_convs),
                'avg_order_value':         compute_aov(total_revenue, total_sales),
                'facebook_aov':            compute_aov(facebook_revenue, facebook_sales),
                'instagram_aov':           compute_aov(instagram_revenue, instagram_sales),
                'revenue_per_client':      compute_revenue_per_client(total_revenue, unique_clients),
                'revenue_goal':            revenue_goal,
                'revenue_gap':             revenue_gap,
                'required_daily_revenue':  required_daily,
                'goal_status':             goal_status,
                'goal_progress_percent':   goal_progress,
                'is_partial':              is_partial,
            }
        )
        logger.info(f"Snapshot computed: {self.tenant.name} | {period_type} | {period_start}")
        return snapshot
