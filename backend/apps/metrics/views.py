from datetime import date, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.common.views import get_tenant
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from apps.tenants.permissions import IsClientOrAdmin
from .models import MetricSnapshot

CACHE_TTL = 900

def _snap(s):
    return {
        'period_type': s.period_type, 'period_start': s.period_start, 'period_end': s.period_end,
        'is_partial': s.is_partial, 'total_revenue': s.total_revenue, 'total_spend': s.total_spend,
        'facebook_revenue': s.facebook_revenue, 'instagram_revenue': s.instagram_revenue,
        'total_sales': s.total_sales, 'total_conversations': s.total_conversations,
        'facebook_sales': s.facebook_sales, 'instagram_sales': s.instagram_sales,
        'roi': s.roi, 'facebook_roi': s.facebook_roi, 'instagram_roi': s.instagram_roi,
        'conversion_rate': s.conversion_rate, 'cost_per_conversation': s.cost_per_conversation,
        'cost_per_sale': s.cost_per_sale, 'avg_order_value': s.avg_order_value,
        'facebook_aov': s.facebook_aov, 'instagram_aov': s.instagram_aov,
        'revenue_per_client': s.revenue_per_client, 'pipeline_open_value': s.pipeline_open_value,
        'revenue_goal': s.revenue_goal, 'revenue_gap': s.revenue_gap,
        'required_daily_revenue': s.required_daily_revenue, 'goal_status': s.goal_status,
        'goal_progress_percent': s.goal_progress_percent, 'computed_at': s.computed_at,
    }

class DashboardMetricsView(APIView):
    permission_classes = [IsAuthenticated, IsClientOrAdmin]
    def get(self, request):
        account = get_tenant(request)
        cache_key = f'dashboard_metrics:{account.id}'
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)
        today = date.today()
        month_start = today.replace(day=1)
        def get_snap(pt, start):
            try:
                return _snap(MetricSnapshot.objects.get(tenant=account, period_type=pt, period_start=start))
            except MetricSnapshot.DoesNotExist:
                return None
        data = {'today': get_snap('day', today), 'month': get_snap('month', month_start),
                'currency': account.currency, 'budget_cap_percent': account.budget_increase_cap_percent}
        cache.set(cache_key, data, CACHE_TTL)
        return Response(data)

class PeriodMetricsView(APIView):
    permission_classes = [IsAuthenticated, IsClientOrAdmin]
    def get(self, request):
        start_str = request.query_params.get('start')
        end_str = request.query_params.get('end')
        period_type = request.query_params.get('period_type', 'month')
        if not start_str or not end_str:
            return Response({'error': True, 'message': 'start and end required.'}, status=400)
        period_start = date.fromisoformat(start_str)
        period_end = date.fromisoformat(end_str)
        try:
            s = MetricSnapshot.objects.get(tenant=get_tenant(request), period_type=period_type, period_start=period_start)
        except MetricSnapshot.DoesNotExist:
            from .services.aggregator import MetricsAggregator
            s = MetricsAggregator(get_tenant(request)).compute_and_store(period_type, period_start, period_end)
        return Response(_snap(s))

class AdPerformanceView(APIView):
    permission_classes = [IsAuthenticated, IsClientOrAdmin]
    def get(self, request):
        from django.db.models import Sum, Count
        from apps.meta_integration.models import Ad
        from apps.meta_integration.models import AdSpendRecord
        from apps.sales.models import Sale
        from apps.metrics.engine import compute_roi, compute_aov, compute_cost_per_sale, compute_roas, compute_cpl, compute_cpa
        today = date.today()
        date_from = request.query_params.get('date_from', today.replace(day=1).isoformat())
        date_to = request.query_params.get('date_to', today.isoformat())
        ads = Ad.objects.filter(campaign__ad_account__tenant=get_tenant(request))
        results = []
        for ad in ads:
            spend = AdSpendRecord.objects.filter(ad=ad, date__range=(date_from, date_to)).aggregate(s=Sum('spend'))['s'] or 0
            sales_agg = Sale.objects.filter(ad=ad, sale_date__range=(date_from, date_to), is_confirmed=True).aggregate(r=Sum('amount'), c=Count('id'))
            revenue = sales_agg['r'] or 0
            sales_count = sales_agg['c'] or 0
            results.append({
                'ad_id': str(ad.id), 'ad_name': ad.name, 'platform': ad.campaign.platform,
                'campaign_name': ad.campaign.name, 'spend': spend, 'revenue': revenue,
                'sales': sales_count, 'roi': compute_roi(revenue, spend),
                'aov': compute_aov(revenue, sales_count), 'cost_per_sale': compute_cost_per_sale(spend, sales_count),
            })
        results.sort(key=lambda x: float(x['revenue'] or 0), reverse=True)
        return Response(results)


class SnapshotView(APIView):
    """
    GET /api/v1/metrics/snapshot/
    Returns live-computed metrics for the current month.
    Falls back to MetricSnapshot if available, otherwise computes from Sales.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.sales.models import Sale
        from apps.revenue_goals.models import RevenueGoal
        from apps.common.views import get_tenant
        from django.utils import timezone
        from django.db.models import Sum, Count, Avg
        import datetime

        tenant = get_tenant(request)
        if not tenant:
            return Response({})

        today      = timezone.now().date()
        month_start = today.replace(day=1)
        # Last day of current month
        if today.month == 12:
            month_end = today.replace(day=31)
        else:
            month_end = (today.replace(month=today.month+1, day=1) - datetime.timedelta(days=1))

        days_in_month  = month_end.day
        days_elapsed   = today.day
        days_remaining = days_in_month - days_elapsed

        # ── Optional custom date range from query params ─────
        date_from_str = request.query_params.get('date_from')
        date_to_str   = request.query_params.get('date_to')
        if date_from_str and date_to_str:
            try:
                month_start = datetime.date.fromisoformat(date_from_str)
                today_end   = datetime.date.fromisoformat(date_to_str)
                days_remaining = max((today_end - today).days + 1, 1)
            except ValueError:
                today_end = today
        else:
            today_end = today

        # ── Sales this month ─────────────────────────────────
        # Include sales where is_confirmed=True OR NULL (legacy rows)
        from django.db.models import Q as SQ
        sales_qs = Sale.objects.filter(
            SQ(is_confirmed=True) | SQ(is_confirmed__isnull=True),
            tenant=tenant,
            sale_date__gte=month_start,
            sale_date__lte=today_end,
        )

        agg = sales_qs.aggregate(
            total=Sum('amount'),
            count=Count('id'),
            avg=Avg('amount'),
        )
        total_revenue = float(agg['total'] or 0)
        sales_count   = agg['count'] or 0
        avg_order_value = float(agg['avg'] or 0)

        # Platform breakdown
        fb_agg = sales_qs.filter(platform_source='facebook').aggregate(
            total=Sum('amount'), avg=Avg('amount'))
        ig_agg = sales_qs.filter(platform_source='instagram').aggregate(
            total=Sum('amount'), avg=Avg('amount'))
        fb_revenue = float(fb_agg['total'] or 0)
        ig_revenue = float(ig_agg['total'] or 0)
        fb_aov = float(fb_agg['avg'] or 0)
        ig_aov = float(ig_agg['avg'] or 0)

        # ── Revenue Goal ─────────────────────────────────────
        goal_obj = RevenueGoal.objects.filter(
            tenant=tenant,
            month=month_start,
        ).first()

        revenue_goal   = float(goal_obj.target_amount) if goal_obj else None
        revenue_gap    = 0.0
        required_daily = 0.0
        goal_progress  = 0.0
        goal_status    = 'no_goal'

        if revenue_goal and revenue_goal > 0:
            revenue_gap   = max(revenue_goal - total_revenue, 0)
            goal_progress = min(round((total_revenue / revenue_goal) * 100, 1), 100)
            required_daily = round(revenue_gap / max(days_remaining, 1), 2) if days_remaining > 0 else 0

            if total_revenue >= revenue_goal:
                goal_status = 'ahead'
            elif goal_progress >= 60:
                goal_status = 'on_track'
            else:
                goal_status = 'behind'

        # ── Try MetricSnapshot for ad spend data ─────────────
        total_spend = 0.0
        roi = 0.0
        try:
            from apps.metrics.models import MetricSnapshot
            snap = MetricSnapshot.objects.filter(
                tenant=tenant, period_type='month', period_start=month_start,
            ).first()
            if snap:
                total_spend = float(snap.total_spend or 0)
                roi         = float(snap.roi or 0)
        except Exception:
            pass

        # Compute ROI from sales if no snapshot
        if total_spend > 0 and roi == 0 and total_revenue > 0:
            roi = round(((total_revenue - total_spend) / total_spend) * 100, 1)

        # Pipeline deal count for CPL calculation
        from apps.pipeline.models import PipelineDeal
        pipeline_count = PipelineDeal.objects.filter(
            tenant=tenant,
            created_at__date__gte=month_start,
            created_at__date__lte=today_end,
        ).count()

        return Response({
            'total_revenue':          total_revenue,
            'facebook_revenue':       fb_revenue,
            'instagram_revenue':      ig_revenue,
            'total_spend':            total_spend,
            'roi':                    roi,
            'avg_order_value':        avg_order_value,
            'facebook_aov':           fb_aov,
            'instagram_aov':          ig_aov,
            'total_conversations':    0,
            'conversion_rate':        0,
            'cost_per_conversation':  0,
            'cost_per_sale':          round(total_spend / sales_count, 2) if sales_count else 0,
            'roas':                   round(total_revenue / total_spend, 2) if total_spend > 0 else 0,
            'cpa':                    round(total_spend / sales_count, 2) if sales_count > 0 and total_spend > 0 else 0,
            'cpl':                    round(total_spend / pipeline_count, 2) if pipeline_count > 0 and total_spend > 0 else 0,
            'pipeline_count':         pipeline_count,
            'total_sales_count':      sales_count,
            'goal_status':            goal_status,
            'goal_progress_percent':  goal_progress,
            'revenue_goal':           revenue_goal,
            'required_daily_revenue': required_daily,
            'revenue_gap':            revenue_gap,
        })


class DailySalesView(APIView):
    """GET /api/v1/metrics/daily/?days=7 — daily revenue for last N days"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.sales.models import Sale
        from django.utils import timezone
        from django.db.models import Sum
        import datetime

        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return Response([])

        days = int(request.query_params.get('days', 7))
        today = timezone.now().date()
        start = today - datetime.timedelta(days=days - 1)

        sales = Sale.objects.filter(
            tenant=tenant,
            sale_date__gte=start,
            sale_date__lte=today,
            is_confirmed=True,
        ).values('sale_date').annotate(amount=Sum('amount')).order_by('sale_date')

        # Fill gaps with 0
        sales_map = {s['sale_date']: float(s['amount'] or 0) for s in sales}
        result = []
        for i in range(days):
            d = start + datetime.timedelta(days=i)
            result.append({'date': d.isoformat(), 'amount': sales_map.get(d, 0)})

        return Response(result)


class AdSpendSummaryView(APIView):
    """
    GET /api/v1/metrics/adspend/
    Returns this month's AdSpendRecord totals broken down by platform
    (facebook, instagram) plus WhatsApp/Messenger/Instagram DM conversations
    from pipeline deals.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.common.views import get_tenant
        from apps.meta_integration.models import AdSpendRecord, Ad
        from apps.pipeline.models import PipelineDeal
        from django.db.models import Sum, Count, Q
        from django.utils import timezone
        import datetime

        tenant = get_tenant(request)
        if not tenant:
            return Response({})

        today       = timezone.now().date()
        month_start = today.replace(day=1)
        days        = int(request.query_params.get('days', 30))
        date_start  = today - datetime.timedelta(days=days - 1)

        # ── AdSpendRecord aggregations ────────────────────────
        def spend_agg(platform_filter):
            return AdSpendRecord.objects.filter(
                ad__campaign__ad_account__tenant=tenant,
                ad__campaign__platform__in=platform_filter,
                date__gte=month_start,
            ).aggregate(
                total_spend       = Sum('spend'),
                total_impressions = Sum('impressions'),
                total_clicks      = Sum('clicks'),
                total_dm_convs    = Sum('dm_conversations'),
            )

        fb = spend_agg(['facebook', 'both'])
        ig = spend_agg(['instagram', 'both'])

        # ── Pipeline deals by source channel ─────────────────
        deals_qs = PipelineDeal.objects.filter(
            tenant=tenant,
            created_at__date__gte=date_start,
        )
        wa_count  = deals_qs.filter(source='whatsapp_webhook').count()
        msg_count = deals_qs.filter(source='messenger_webhook').count()
        ig_count  = deals_qs.filter(source='instagram_webhook').count()
        total_deals = deals_qs.count()

        # ── Daily breakdown for chart ─────────────────────────
        daily = []
        for i in range(min(days, 30)):
            d = date_start + datetime.timedelta(days=i)
            day_fb = AdSpendRecord.objects.filter(
                ad__campaign__ad_account__tenant=tenant,
                ad__campaign__platform__in=['facebook','both'],
                date=d,
            ).aggregate(s=Sum('spend'), i=Sum('impressions'), c=Sum('clicks'), d=Sum('dm_conversations'))
            day_ig = AdSpendRecord.objects.filter(
                ad__campaign__ad_account__tenant=tenant,
                ad__campaign__platform__in=['instagram','both'],
                date=d,
            ).aggregate(s=Sum('spend'), i=Sum('impressions'), c=Sum('clicks'), d=Sum('dm_conversations'))
            daily.append({
                'date': d.isoformat(),
                'facebook_spend':       float(day_fb['s'] or 0),
                'facebook_impressions': int(day_fb['i'] or 0),
                'facebook_clicks':      int(day_fb['c'] or 0),
                'facebook_dm_convs':    int(day_fb['d'] or 0),
                'instagram_spend':      float(day_ig['s'] or 0),
                'instagram_impressions':int(day_ig['i'] or 0),
                'instagram_clicks':     int(day_ig['c'] or 0),
                'instagram_dm_convs':   int(day_ig['d'] or 0),
            })

        return Response({
            'period': {'start': date_start.isoformat(), 'end': today.isoformat(), 'days': days},
            'facebook': {
                'spend':        float(fb['total_spend'] or 0),
                'impressions':  int(fb['total_impressions'] or 0),
                'clicks':       int(fb['total_clicks'] or 0),
                'dm_conversations': int(fb['total_dm_convs'] or 0),
            },
            'instagram': {
                'spend':        float(ig['total_spend'] or 0),
                'impressions':  int(ig['total_impressions'] or 0),
                'clicks':       int(ig['total_clicks'] or 0),
                'dm_conversations': int(ig['total_dm_convs'] or 0),
            },
            'conversations': {
                'whatsapp':  wa_count,
                'messenger': msg_count,
                'instagram': ig_count,
                'total':     total_deals,
            },
            'daily': daily,
        })
