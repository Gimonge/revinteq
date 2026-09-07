from celery import shared_task
import logging
logger = logging.getLogger(__name__)

@shared_task
def compute_all_snapshots():
    from datetime import date, timedelta
    from apps.tenants.models import Tenant
    from .services.aggregator import MetricsAggregator
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    count = 0
    for tenant in Tenant.objects.all():
        try:
            agg = MetricsAggregator(tenant)
            agg.compute_and_store('day', today, today)
            agg.compute_and_store('week', week_start, today)
            agg.compute_and_store('month', month_start, today)
            count += 1
        except Exception as e:
            logger.exception(f"Metrics failed for {tenant.name}: {e}")
    return {'computed': count}

@shared_task
def invalidate_dashboard_cache(tenant_id: str):
    from django.core.cache import cache
    cache.delete(f'dashboard_metrics:{tenant_id}')
