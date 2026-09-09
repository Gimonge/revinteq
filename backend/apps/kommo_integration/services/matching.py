"""
Revinteq v3 — Kommo Matching Service

Both Kommo and Revinteq receive the same Meta ad-click event independently.
This service finds the Kommo lead that corresponds to a given PipelineDeal:

  - WhatsApp clicks: match by phone number (Kommo's contact search)
  - Messenger/Instagram clicks: no phone/name captured today, so match by
    the nearest-in-time lead created in the tenant's Kommo account
    (best-effort — flagged for manual review if more than one candidate)

KOMMO_MATCH_WINDOW_MINUTES controls how far after the click we'll still
consider a Kommo lead a match. Retries give Kommo's own webhook time to
create the lead first.
"""
import logging
from datetime import timedelta
from django.conf import settings
from django.utils import timezone

from .kommo_api import KommoAPIClient, KommoAPIError

logger = logging.getLogger(__name__)

WON_STATUS_ID  = 142   # Kommo system status — constant across all pipelines
LOST_STATUS_ID = 143

MATCH_WINDOW_MINUTES = getattr(settings, 'KOMMO_MATCH_WINDOW_MINUTES', 20)
MAX_MATCH_ATTEMPTS   = getattr(settings, 'KOMMO_MATCH_MAX_RETRIES', 5)


def attempt_match(matched_lead) -> bool:
    """
    Try to find the Kommo lead for one KommoMatchedLead's pipeline_deal.
    Returns True if matched (caller decides whether to keep retrying on False).
    """
    deal   = matched_lead.pipeline_deal
    tenant = matched_lead.tenant

    try:
        connection = tenant.kommo_connection
    except Exception:
        matched_lead.status = 'unmatched'
        matched_lead.save(update_fields=['status'])
        return False

    if not connection.sync_enabled:
        return False

    client = KommoAPIClient.for_connection(connection)
    matched_lead.match_attempts += 1
    matched_lead.last_checked = timezone.now()

    candidate = None
    method = None

    if deal.source == 'whatsapp_webhook' and deal.customer_phone:
        method = 'phone'
        leads = client.find_leads_by_phone(deal.customer_phone)
        # Prefer the lead closest in time to our own click
        candidate = _closest_by_time(leads, deal.new_click_at)
    else:
        method = 'time_window'
        window_start = deal.new_click_at - timedelta(minutes=2)
        since_ts = int(window_start.timestamp())
        leads = client.get_leads(updated_since=since_ts)
        candidates = _leads_within_window(leads, deal.new_click_at, minutes=5)
        if len(candidates) > 1:
            logger.warning(
                f"Kommo match ambiguous for deal {deal.id}: "
                f"{len(candidates)} leads in time window — picking nearest, flag for review"
            )
        candidate = _closest_by_time(candidates, deal.new_click_at)

    if candidate:
        matched_lead.kommo_lead_id = str(candidate['id'])
        matched_lead.match_method  = method
        matched_lead.status        = 'matched'
        matched_lead.matched_at    = timezone.now()
        matched_lead.raw_lead_data = candidate
        matched_lead.save()
        return True

    if matched_lead.match_attempts >= MAX_MATCH_ATTEMPTS:
        matched_lead.status = 'unmatched'
    matched_lead.save(update_fields=['match_attempts', 'last_checked', 'status'])
    return False


def _closest_by_time(leads: list, reference_time) -> dict:
    if not leads:
        return None
    reference_ts = reference_time.timestamp()
    return min(leads, key=lambda l: abs(l.get('created_at', 0) - reference_ts))


def _leads_within_window(leads: list, reference_time, minutes: int) -> list:
    reference_ts = reference_time.timestamp()
    window = minutes * 60
    return [l for l in leads if abs(l.get('created_at', 0) - reference_ts) <= window]


def check_and_sync_won(matched_lead) -> bool:
    """
    For an already-matched lead, check its current Kommo status. If it's
    now Won, create the Sale. Returns True if a Sale was created this call.
    """
    from apps.sales.models import Sale

    tenant = matched_lead.tenant
    connection = tenant.kommo_connection
    client = KommoAPIClient.for_connection(connection)

    lead = client.get_lead(matched_lead.kommo_lead_id)
    matched_lead.raw_lead_data = lead
    matched_lead.last_checked  = timezone.now()

    status_id = lead.get('status_id')
    if status_id == LOST_STATUS_ID:
        matched_lead.status = 'lost'
        matched_lead.save(update_fields=['status', 'raw_lead_data', 'last_checked'])
        return False

    if status_id != WON_STATUS_ID:
        matched_lead.save(update_fields=['raw_lead_data', 'last_checked'])
        return False

    if matched_lead.sale_id:
        return False  # already synced

    deal   = matched_lead.pipeline_deal
    amount = lead.get('price') or 0
    closed_at = lead.get('closed_at')
    sale_date = timezone.datetime.fromtimestamp(closed_at).date() if closed_at else timezone.now().date()

    platform_source = deal.platform if deal.platform in ('facebook', 'instagram') else 'other'

    sale = Sale.objects.create(
        tenant          = tenant,
        pipeline_deal   = deal,
        ad              = deal.ad,
        campaign        = deal.campaign,
        customer_name   = deal.customer_name,
        customer_phone  = deal.customer_phone,
        product_name    = lead.get('name') or 'Kommo deal',
        amount          = amount,
        payment_method  = 'other',
        platform_source = platform_source,
        sale_date       = sale_date,
        is_confirmed    = True,
        notes           = f"Synced from Kommo lead #{matched_lead.kommo_lead_id} (Won)",
    )

    matched_lead.sale       = sale
    matched_lead.status     = 'won'
    matched_lead.won_amount = amount
    matched_lead.won_at     = timezone.now()
    matched_lead.save()

    logger.info(f"Kommo won-deal synced as Sale {sale.id} for tenant {tenant.name}")
    return True
