from celery import shared_task
import logging
logger = logging.getLogger(__name__)

@shared_task
def run_all_recommendations():
    from apps.tenants.models import Tenant
    from .engine import RecommendationEngine
    count = 0
    for tenant in Tenant.objects.filter(status__in=['active','trial']):
        try:
            RecommendationEngine(tenant).run()
            count += 1
        except Exception as e:
            logger.exception(f"Rec engine failed for {tenant.name}: {e}")
    return {'processed': count}

@shared_task
def create_r05_recommendation(tenant_id: str, stale_count: int):
    from apps.tenants.models import Tenant
    from .engine import RecommendationEngine
    try:
        RecommendationEngine(Tenant.objects.get(id=tenant_id)).run_r05(stale_count)
    except Tenant.DoesNotExist:
        logger.error(f"Tenant {tenant_id} not found for R05")

@shared_task
def create_r07_recommendation(ad_account_id: str, days_left: int):
    from apps.meta_integration.models import AdAccount
    from .engine import RecommendationEngine
    try:
        acc = AdAccount.objects.select_related('tenant').get(id=ad_account_id)
        RecommendationEngine(acc.tenant).run_r07(days_left, acc.platform)
    except AdAccount.DoesNotExist:
        logger.error(f"AdAccount {ad_account_id} not found for R07")
