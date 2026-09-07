"""Revinteq v3 — External API Celery Tasks"""
import json, hmac, hashlib, logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def dispatch_webhook(self, tenant_id: str, event: str, payload: dict):
    """
    Deliver a webhook event to all registered endpoints for a tenant.
    Retries up to 5 times with exponential backoff.
    """
    import requests
    from apps.external_api.models import WebhookEndpoint, WebhookDelivery

    endpoints = WebhookEndpoint.objects.filter(
        tenant_id=tenant_id,
        is_active=True,
    )

    for endpoint in endpoints:
        if hasattr(endpoint, 'events') and endpoint.events and event not in endpoint.events:
            continue

        full_payload = {
            'event':     event,
            'tenant_id': tenant_id,
            'data':      payload,
            'timestamp': timezone.now().isoformat(),
        }

        body = json.dumps(full_payload)
        secret = getattr(endpoint, 'secret', '') or ''
        signature = hmac.new(
            secret.encode(), body.encode(), hashlib.sha256
        ).hexdigest()

        delivery = WebhookDelivery.objects.create(
            endpoint=endpoint,
            event=event,
            payload=full_payload,
            status='pending',
        )

        try:
            response = requests.post(
                endpoint.url,
                data=body,
                headers={
                    'Content-Type':         'application/json',
                    'X-Revinteq-Signature': f'sha256={signature}',
                    'X-Revinteq-Event':     event,
                },
                timeout=10,
            )
            delivery.response_status_code = response.status_code
            delivery.response_body        = response.text[:500]
            delivery.status               = 'success' if response.ok else 'failed'
            delivery.delivered_at         = timezone.now()
            delivery.attempt_count        = getattr(delivery, 'attempt_count', 0) + 1
            delivery.save()

        except requests.RequestException as exc:
            delivery.status       = 'failed'
            delivery.response_body= str(exc)[:500]
            delivery.attempt_count= getattr(delivery, 'attempt_count', 0) + 1
            delivery.save()
            raise self.retry(exc=exc)
