"""
Revinteq v3 — WhatsApp / Messenger / Instagram DM Webhook Tasks

Pipeline deal creation rules:
  - Only fires on message.referral with source_type='ad' (CTA button click)
  - Deduplication: same phone + same ad within 7 days = skip (not a new lead)
  - Velocity scoring: based on EAT time-of-day + repeat visitor check
  - Estimated value: pulled from campaign daily_budget as a proxy
"""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


# ── Velocity Scoring ──────────────────────────────────────────────────────────

def _score_velocity(click_time, customer_phone: str, tenant_id: str) -> str:
    """
    Score velocity based on:
      1. EAT time-of-day (morning/evening = hot, afternoon = warm, night = cold)
      2. Weekday vs weekend (weekends downgraded one level)
      3. Repeat visitor — phone already in open pipeline = warm not hot
    """
    from apps.pipeline.models import PipelineDeal
    try:
        import pytz
        eat = pytz.timezone('Africa/Nairobi')
        local = click_time.astimezone(eat)
    except Exception:
        local = click_time  # Fallback if pytz not available

    hour    = local.hour
    weekday = local.weekday()  # 0=Monday, 6=Sunday

    # Time-of-day score
    if 8 <= hour <= 12 or 19 <= hour <= 22:
        score = 'hot'    # Morning peak + evening shopping window
    elif 13 <= hour <= 18:
        score = 'warm'   # Afternoon browsing
    else:
        score = 'cold'   # Late night / pre-dawn

    # Weekend downgrade
    if weekday >= 5 and score == 'hot':
        score = 'warm'

    # Repeat visitor check — already in open pipeline means lower urgency
    if customer_phone:
        try:
            already_open = PipelineDeal.objects.filter(
                tenant_id=tenant_id,
                customer_phone=customer_phone,
                stage__in=['new_click', 'contacted', 'interested', 'negotiating'],
            ).exists()
            if already_open and score == 'hot':
                score = 'warm'
        except Exception:
            pass

    return score


# ── Deduplication ─────────────────────────────────────────────────────────────

def _is_duplicate(phone: str, meta_ad_id: str, tenant_id: str, window_days: int = 7) -> bool:
    """
    Returns True if the same phone number clicked the same ad within window_days.
    This catches retargeting re-clicks from the same person — we don't want
    two pipeline deals for the same person on the same ad in the same week.
    """
    if not phone:
        return False
    from apps.pipeline.models import PipelineDeal
    from apps.meta_integration.models import Ad
    from datetime import timedelta
    cutoff = timezone.now() - timedelta(days=window_days)
    try:
        ad = Ad.objects.get(meta_ad_id=meta_ad_id)
        return PipelineDeal.objects.filter(
            tenant_id=tenant_id,
            customer_phone=phone,
            ad=ad,
            created_at__gte=cutoff,
        ).exists()
    except Exception:
        return False


# ── Kommo matching hook ────────────────────────────────────────────────────────

def _start_kommo_match(deal):
    """
    If this tenant has Kommo connected, create a pending match record and
    dispatch the async matching task (delayed, so Kommo's own independent
    webhook has a head start creating its lead for the same click).
    """
    try:
        if not hasattr(deal.tenant, 'kommo_connection') or not deal.tenant.kommo_connection.sync_enabled:
            return
        from apps.kommo_integration.models import KommoMatchedLead
        from apps.kommo_integration.tasks import match_pipeline_deal_to_kommo

        matched_lead, _ = KommoMatchedLead.objects.get_or_create(
            pipeline_deal=deal,
            defaults={'tenant': deal.tenant},
        )
        match_pipeline_deal_to_kommo.apply_async(args=[str(matched_lead.id)], countdown=30)
    except Exception as e:
        logger.warning(f"Could not start Kommo match for deal {deal.id}: {e}")


# ── WhatsApp Webhook ──────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_whatsapp_webhook(self, payload: dict):
    """
    Process WhatsApp Business API webhook.
    Only creates pipeline deals for messages with ad referrals (CTA button clicks).

    Referral object is ONLY present when the customer tapped the
    'Send Message' / 'WhatsApp' button on a Meta ad — not organic messages.
    """
    try:
        for entry in payload.get('entry', []):
            for change in entry.get('changes', []):
                value    = change.get('value', {})
                messages = value.get('messages', [])
                contacts = value.get('contacts', [])
                metadata = value.get('metadata', {})

                contact_map = {
                    c.get('wa_id', ''): c.get('profile', {}).get('name', '')
                    for c in contacts if c.get('wa_id')
                }

                for message in messages:
                    referral = message.get('referral')
                    if not referral:
                        continue  # Not from an ad — ignore

                    source_type = referral.get('source_type', '')
                    if source_type not in ('ad', 'post'):
                        continue

                    _handle_whatsapp_ad_click(
                        meta_ad_id   = referral.get('source_id', ''),
                        message_id   = message.get('id', ''),
                        sender_phone = message.get('from', ''),
                        sender_name  = contact_map.get(message.get('from', ''), ''),
                        click_time   = timezone.now(),
                        referral     = referral,
                    )

    except Exception as exc:
        logger.exception(f"WhatsApp webhook error: {exc}")
        raise self.retry(exc=exc)


def _handle_whatsapp_ad_click(
    meta_ad_id:   str,
    message_id:   str,
    sender_phone: str,
    sender_name:  str,
    click_time,
    referral:     dict,
):
    from apps.meta_integration.models import Ad
    from apps.pipeline.models import PipelineDeal
    from apps.customers.models import Customer

    # 1. Dedup by exact message ID (same message replayed)
    if message_id and PipelineDeal.objects.filter(whatsapp_message_id=message_id).exists():
        logger.info(f"Duplicate WhatsApp message ignored: {message_id}")
        return

    # 2. Find the ad
    try:
        ad = Ad.objects.select_related('campaign__ad_account__tenant').get(
            meta_ad_id=meta_ad_id
        )
    except Ad.DoesNotExist:
        logger.warning(
            f"WhatsApp click: ad not synced yet (meta_ad_id={meta_ad_id}). "
            f"Deal will be created when ad syncs. Phone: {sender_phone}"
        )
        # Queue a retry — the ad might not be synced yet
        _queue_pending_click(meta_ad_id, message_id, sender_phone, sender_name, referral)
        return

    tenant = ad.campaign.ad_account.tenant

    # 3. Dedup by phone + ad within 7 days (same person, same ad, retargeting)
    if _is_duplicate(sender_phone, meta_ad_id, str(tenant.id), window_days=7):
        logger.info(
            f"Duplicate retargeting click ignored: "
            f"phone={sender_phone} ad={ad.name} tenant={tenant.name}"
        )
        return

    # 4. Determine platform
    source_url = referral.get('source_url', '')
    platform   = ad.campaign.platform
    if platform == 'both':
        platform = 'instagram' if 'instagram' in source_url.lower() else 'facebook'

    # 5. Score velocity intelligently
    velocity = _score_velocity(click_time, sender_phone, str(tenant.id))

    # 6. Estimate deal value from campaign daily budget (rough proxy)
    estimated_value = None
    try:
        if ad.campaign.daily_budget:
            # Rough proxy: 3x the daily budget = expected revenue per customer
            estimated_value = ad.campaign.daily_budget * 3
    except Exception:
        pass

    # 7. Create deal
    deal = PipelineDeal.objects.create(
        tenant            = tenant,
        ad                = ad,
        campaign          = ad.campaign,
        platform          = platform,
        stage             = 'new_click',
        source            = 'whatsapp_webhook',
        whatsapp_message_id = message_id,
        customer_name     = sender_name,
        customer_phone    = sender_phone,
        new_click_at      = click_time,
        velocity          = velocity,
        estimated_value   = estimated_value,
        notes             = (
            f"Auto-created from WhatsApp ad click. "
            f"Ad: {ad.name} | Platform: {platform} | "
            f"Velocity scored: {velocity.upper()} "
            f"({'business hours' if velocity=='hot' else 'off-peak'})"
        ),
    )

    # 8. Auto-create/update Customer record
    try:
        Customer.get_or_create_from_deal(deal)
    except Exception as e:
        logger.warning(f"Customer creation failed: {e}")

    logger.info(
        f"✅ Pipeline deal created | Tenant={tenant.name} | Ad={ad.name} | "
        f"Platform={platform} | Velocity={velocity.upper()} | "
        f"Phone={sender_phone} | Deal={deal.id}"
    )

    # 8b. Kick off Kommo lead matching (Kommo receives the same ad click
    # independently and creates its own lead — we look it up so a later
    # "won" status there can be attributed back to this ad/campaign)
    _start_kommo_match(deal)

    # 9. Fire external webhook
    try:
        from apps.external_api.tasks import dispatch_webhook
        dispatch_webhook.delay(str(tenant.id), 'pipeline.new_click', {
            'deal_id':   str(deal.id),
            'platform':  platform,
            'ad_name':   ad.name,
            'velocity':  velocity,
            'source':    'whatsapp_webhook',
        })
    except Exception:
        pass

    # 10. Auto-SMS follow-up
    try:
        from apps.sms.tasks import send_auto_sms
        send_auto_sms.delay(
            tenant_id = str(tenant.id),
            trigger   = 'pipeline.new_click',
            context   = {
                'customer_name':    sender_name or 'Valued Customer',
                'phone':            sender_phone,
                'deal_id':          str(deal.id),
                'mpesa_reference':  deal.mpesa_reference,
                'ad_name':          ad.name,
                'velocity':         velocity,
            }
        )
    except Exception:
        pass

    return deal


def _queue_pending_click(meta_ad_id, message_id, phone, name, referral):
    """
    Store the click temporarily so it can be retried after ad sync completes.
    Uses a simple retry via Celery delay.
    """
    retry_pending_click.apply_async(
        args=[meta_ad_id, message_id, phone, name, referral],
        countdown=300,  # Retry after 5 minutes to allow ad sync to complete
    )


@shared_task(max_retries=2, default_retry_delay=600)
def retry_pending_click(meta_ad_id, message_id, phone, name, referral):
    """Retry a WhatsApp click that arrived before the ad was synced."""
    _handle_whatsapp_ad_click(
        meta_ad_id   = meta_ad_id,
        message_id   = message_id,
        sender_phone = phone,
        sender_name  = name,
        click_time   = timezone.now(),
        referral     = referral,
    )


# ── Messenger Webhook ─────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_messenger_webhook(self, payload: dict):
    """
    Process Facebook Messenger webhook.
    Only creates deals for messages from Click to Messenger ads
    (referral.source == 'ADS').
    """
    try:
        for entry in payload.get('entry', []):
            for messaging in entry.get('messaging', []):
                referral = (
                    messaging.get('referral') or
                    messaging.get('postback', {}).get('referral')
                )
                if not referral or referral.get('source') != 'ADS':
                    continue

                meta_ad_id = referral.get('ad_id', '')
                sender_id  = messaging.get('sender', {}).get('id', '')
                if not meta_ad_id:
                    continue

                _handle_channel_click(
                    meta_ad_id   = meta_ad_id,
                    thread_id    = sender_id,
                    sender_name  = '',
                    sender_phone = '',
                    channel      = 'messenger',
                    source       = 'messenger_webhook',
                    dedup_field  = 'messenger_thread_id',
                )
    except Exception as exc:
        logger.exception(f"Messenger webhook error: {exc}")
        raise self.retry(exc=exc)


# ── Instagram DM Webhook ──────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_instagram_webhook(self, payload: dict):
    """
    Process Instagram DM webhook.
    Only creates deals for Click to Instagram DM ad interactions
    (referral.source == 'ADS').
    Requires instagram_manage_messages Advanced Access on the Meta App.
    """
    try:
        for entry in payload.get('entry', []):
            for messaging in entry.get('messaging', []):
                referral = messaging.get('referral')
                if not referral or referral.get('source') != 'ADS':
                    continue

                meta_ad_id = referral.get('ad_id', '')
                sender_id  = messaging.get('sender', {}).get('id', '')
                if not meta_ad_id:
                    continue

                _handle_channel_click(
                    meta_ad_id   = meta_ad_id,
                    thread_id    = sender_id,
                    sender_name  = '',
                    sender_phone = '',
                    channel      = 'instagram',
                    source       = 'instagram_webhook',
                    dedup_field  = 'instagram_thread_id',
                )
    except Exception as exc:
        logger.exception(f"Instagram webhook error: {exc}")
        raise self.retry(exc=exc)


# ── Shared channel handler ────────────────────────────────────────────────────

def _handle_channel_click(
    meta_ad_id:  str,
    thread_id:   str,
    sender_name: str,
    sender_phone:str,
    channel:     str,
    source:      str,
    dedup_field: str,
):
    from apps.meta_integration.models import Ad
    from apps.pipeline.models import PipelineDeal
    from apps.customers.models import Customer

    # Dedup by thread ID (exact replay)
    if thread_id and PipelineDeal.objects.filter(**{dedup_field: thread_id}).exists():
        logger.info(f"Duplicate {channel} thread ignored: {thread_id}")
        return

    try:
        ad = Ad.objects.select_related('campaign__ad_account__tenant').get(
            meta_ad_id=meta_ad_id
        )
    except Ad.DoesNotExist:
        logger.warning(f"{channel} click: ad not found meta_ad_id={meta_ad_id}")
        return

    tenant   = ad.campaign.ad_account.tenant
    now      = timezone.now()
    velocity = _score_velocity(now, sender_phone, str(tenant.id))

    estimated_value = None
    try:
        if ad.campaign.daily_budget:
            estimated_value = ad.campaign.daily_budget * 3
    except Exception:
        pass

    kwargs = {
        'tenant':         tenant,
        'ad':             ad,
        'campaign':       ad.campaign,
        'platform':       channel,
        'stage':          'new_click',
        'source':         source,
        'customer_name':  sender_name,
        'customer_phone': sender_phone,
        'new_click_at':   now,
        'velocity':       velocity,
        'estimated_value': estimated_value,
        dedup_field:      thread_id,
        'notes': (
            f"Auto-created from {channel.title()} ad click. "
            f"Ad: {ad.name} | Velocity: {velocity.upper()}"
        ),
    }
    deal = PipelineDeal.objects.create(**kwargs)

    try:
        Customer.get_or_create_from_deal(deal)
    except Exception as e:
        logger.warning(f"Customer creation failed for {channel}: {e}")

    logger.info(
        f"✅ {channel.title()} deal | Tenant={tenant.name} | "
        f"Ad={ad.name} | Velocity={velocity.upper()} | Deal={deal.id}"
    )

    # Kick off Kommo lead matching (best-effort — no phone/name captured
    # for Messenger/Instagram, so this matches by nearest-in-time instead)
    _start_kommo_match(deal)

    try:
        from apps.external_api.tasks import dispatch_webhook
        dispatch_webhook.delay(str(tenant.id), 'pipeline.new_click', {
            'deal_id': str(deal.id), 'platform': channel,
            'velocity': velocity, 'source': source,
        })
    except Exception:
        pass

    if sender_phone:
        try:
            from apps.sms.tasks import send_auto_sms
            send_auto_sms.delay(
                tenant_id=str(tenant.id),
                trigger='pipeline.new_click',
                context={
                    'customer_name':   sender_name or 'Valued Customer',
                    'phone':           sender_phone,
                    'deal_id':         str(deal.id),
                    'mpesa_reference': deal.mpesa_reference,
                    'ad_name':         ad.name,
                    'velocity':        velocity,
                }
            )
        except Exception:
            pass

    return deal
