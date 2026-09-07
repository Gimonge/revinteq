"""Revinteq v3 — SMS Celery Tasks"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_auto_sms(self, tenant_id: str, trigger: str, context: dict):
    """
    Send an automatic SMS based on a trigger event.
    Looks up the SMSTrigger for this tenant + trigger combo.
    """
    try:
        from apps.tenants.models import Tenant
        from apps.sms.models import SMSConfig, SMSTrigger
        from apps.sms.services.africastalking import ATSMSService

        tenant = Tenant.objects.get(id=tenant_id)

        # Check if trigger is configured and active
        try:
            trigger_config = SMSTrigger.objects.get(
                tenant=tenant, trigger=trigger, is_active=True
            )
        except SMSTrigger.DoesNotExist:
            return {'skipped': True, 'reason': f'No active trigger for {trigger}'}

        # Get SMS config
        try:
            sms_config = SMSConfig.objects.get(tenant=tenant, is_active=True)
        except SMSConfig.DoesNotExist:
            return {'skipped': True, 'reason': 'No SMS config for tenant'}

        # Get recipient phone from context
        phone = context.get('phone') or context.get('recipient_phone')
        if not phone:
            # Try to get phone from pipeline deal
            deal_id = context.get('deal_id')
            if deal_id:
                from apps.pipeline.models import PipelineDeal
                deal = PipelineDeal.objects.filter(id=deal_id).first()
                if deal:
                    phone = deal.customer_phone or ''

        if not phone:
            return {'skipped': True, 'reason': 'No recipient phone number'}

        message = trigger_config.render_message(context)
        service = ATSMSService(sms_config)
        log = service.send(
            recipient=phone,
            message=message,
            tenant=tenant,
            source='auto',
            trigger=trigger,
        )

        logger.info(f"Auto-SMS sent for trigger '{trigger}' to {phone}: status={log.status}")
        return {'sent': True, 'message_id': str(log.id), 'status': log.status}

    except Exception as exc:
        logger.exception(f"Auto-SMS task failed: {exc}")
        raise self.retry(exc=exc)


@shared_task
def send_cold_deal_sms():
    """
    Hourly: check for deals that went cold (3+ days, no movement).
    Send auto-SMS follow-up if trigger is configured.
    """
    from apps.pipeline.models import PipelineDeal
    from apps.tenants.models import Tenant

    stale_deals = PipelineDeal.objects.filter(
        stage__in=['new_click', 'contacted', 'interested', 'negotiating'],
        days_in_current_stage=3,  # Exactly 3 days — send once
    ).select_related('tenant')

    for deal in stale_deals:
        send_auto_sms.delay(
            tenant_id=str(deal.tenant.id),
            trigger='deal_went_cold',
            context={
                'customer_name': deal.customer_name or 'Valued Customer',
                'phone': getattr(deal, 'customer_phone', ''),
                'deal_id': str(deal.id),
            }
        )

    return {'deals_processed': stale_deals.count()}
