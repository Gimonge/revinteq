"""Revinteq v3 — Kommo Integration Celery Tasks"""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def match_pipeline_deal_to_kommo(self, matched_lead_id: str):
    """
    Try to find the Kommo lead for this deal. Retries with backoff so
    Kommo's own (independent) webhook has time to create its lead first —
    the two systems receive the ad-click event in parallel, not in order.
    """
    from .models import KommoMatchedLead
    from .services.matching import attempt_match

    try:
        matched_lead = KommoMatchedLead.objects.select_related('pipeline_deal', 'tenant').get(id=matched_lead_id)
    except KommoMatchedLead.DoesNotExist:
        logger.warning(f"KommoMatchedLead {matched_lead_id} not found")
        return

    if matched_lead.status != 'pending':
        return

    try:
        found = attempt_match(matched_lead)
    except Exception as exc:
        logger.exception(f"Kommo match attempt failed: {exc}")
        raise self.retry(exc=exc, countdown=60)

    if not found and matched_lead.match_attempts < 5:
        # Retry with increasing delay: 30s, 60s, 2m, 5m, 10m
        delays = [30, 60, 120, 300, 600]
        countdown = delays[min(matched_lead.match_attempts - 1, len(delays) - 1)]
        raise self.retry(countdown=countdown)


@shared_task
def sync_matched_leads_for_tenant(tenant_id: str):
    """Check every currently-matched (not yet won/lost) lead for status changes."""
    from .models import KommoMatchedLead
    from .services.matching import check_and_sync_won

    leads = KommoMatchedLead.objects.filter(tenant_id=tenant_id, status='matched')
    synced = 0
    for lead in leads:
        try:
            if check_and_sync_won(lead):
                synced += 1
        except Exception as e:
            logger.warning(f"Kommo sync check failed for {lead.id}: {e}")
    return {'checked': leads.count(), 'synced': synced}


@shared_task
def sync_all_kommo_connections():
    """Nightly — check all tenants' matched leads for won/lost status changes."""
    from .models import KommoConnection
    connections = KommoConnection.objects.filter(sync_enabled=True)
    for conn in connections:
        sync_matched_leads_for_tenant.delay(str(conn.tenant_id))
        conn.last_synced = timezone.now()
        conn.save(update_fields=['last_synced'])
    return {'dispatched': connections.count()}


@shared_task
def refresh_expiring_kommo_tokens():
    """Every few hours — proactively refresh tokens nearing their 24h expiry."""
    from datetime import timedelta
    from .models import KommoConnection
    from .services.matching import refresh_connection_token

    threshold = timezone.now() + timedelta(hours=2)
    expiring = KommoConnection.objects.filter(
        sync_enabled=True,
        token_expires_at__lte=threshold,
    )
    refreshed = 0
    for conn in expiring:
        try:
            refresh_connection_token(conn)
            refreshed += 1
        except Exception as e:
            logger.warning(f"Kommo token refresh failed for {conn.tenant.name}: {e}")
    return {'checked': expiring.count(), 'refreshed': refreshed}
