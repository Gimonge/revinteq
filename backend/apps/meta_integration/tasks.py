"""Revinteq v3 — Meta Integration Celery Tasks"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_ad_account(self, ad_account_id: str, days_back: int = 30):
    from .models import AdAccount
    from .services.ingestion import MetaIngestionService
    try:
        account = AdAccount.objects.get(id=ad_account_id)
        service = MetaIngestionService(account)
        result  = service.sync_full(days_back=days_back)
        logger.info(f"Sync done: {account.meta_account_id} — {result}")
        return result
    except AdAccount.DoesNotExist:
        logger.error(f"AdAccount {ad_account_id} not found")
        return {'error': 'not found'}
    except Exception as exc:
        logger.exception(f"Sync failed: {exc}")
        raise self.retry(exc=exc)


@shared_task
def sync_all_for_tenant(tenant_id: str):
    from .models import AdAccount
    accounts = AdAccount.objects.filter(tenant_id=tenant_id, sync_enabled=True)
    for acc in accounts:
        sync_ad_account.delay(str(acc.id), days_back=7)
    return {'dispatched': accounts.count()}


@shared_task
def sync_all_accounts():
    """Nightly 02:00 EAT — sync every active ad account."""
    from .models import AdAccount
    accounts = AdAccount.objects.filter(sync_enabled=True)
    for acc in accounts:
        sync_ad_account.delay(str(acc.id), days_back=2)
    logger.info(f"Nightly sync dispatched for {accounts.count()} accounts")
    return {'dispatched': accounts.count()}


@shared_task
def check_token_expiry():
    """Daily 08:00 EAT — warn about tokens expiring within 7 days."""
    from django.utils import timezone
    from datetime import timedelta
    from .models import AdAccount
    threshold  = timezone.now() + timedelta(days=7)
    expiring   = AdAccount.objects.filter(
        sync_enabled=True,
        token_expires_at__lte=threshold,
        token_expires_at__gt=timezone.now(),
    )
    for acc in expiring:
        days = acc.days_until_token_expiry
        if days is not None:
            from apps.recommendations.tasks import create_r07_recommendation
            create_r07_recommendation.delay(str(acc.id), days)
    return {'expiring_soon': expiring.count()}
