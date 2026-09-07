"""Revinteq v3 — M-Pesa Celery Tasks"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def match_mpesa_transaction(self, transaction_id: str):
    """Match an incoming M-Pesa transaction to a pipeline deal."""
    try:
        from apps.mpesa.models import MPesaTransaction
        from apps.mpesa.services.matcher import MPesaTransactionMatcher
        transaction = MPesaTransaction.objects.get(id=transaction_id)
        matcher = MPesaTransactionMatcher(transaction)
        result = matcher.match_and_process()
        logger.info(f"M-Pesa match result: {result}")
        return result
    except Exception as exc:
        logger.exception(f"M-Pesa matching failed for {transaction_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task
def register_mpesa_c2b_urls(config_id: str):
    """Register C2B callback URLs with Safaricom Daraja."""
    try:
        from django.conf import settings
        from apps.mpesa.models import MPesaConfig
        from apps.mpesa.services.daraja import DarajaClient

        config = MPesaConfig.objects.select_related('tenant').get(id=config_id)
        client = DarajaClient(config)

        site_url = settings.SITE_URL
        slug = config.tenant.slug

        confirmation_url = f"{site_url}/api/v1/mpesa/callback/confirmation/{slug}/"
        validation_url = f"{site_url}/api/v1/mpesa/callback/validation/{slug}/"

        result = client.register_c2b_urls(confirmation_url, validation_url)
        logger.info(f"C2B URLs registered for {config.tenant.name}: {result}")
        return result

    except Exception as e:
        logger.exception(f"Failed to register C2B URLs for config {config_id}: {e}")
