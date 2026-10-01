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

sync_unmatched_won_leads handles the other case: a Won Kommo lead with no
matched ad click at all (e.g. Meta isn't connected yet, or it came in
organically) — those still become Sales, just without ad/campaign
attribution.
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


def refresh_pipeline_cache(connection, force=False) -> dict:
    """
    Fetch and cache this tenant's own Kommo pipeline structure — every
    client names/orders their stages differently (e.g. "Qualified HOT",
    "Discovery Call Booked"), so we look it up rather than assume one.
    Cached for a day unless force=True; the funnel view reads from cache.
    """
    if not force and connection.pipeline_cache and connection.pipeline_cache_updated_at:
        age = timezone.now() - connection.pipeline_cache_updated_at
        if age < timedelta(hours=24):
            return connection.pipeline_cache

    client = KommoAPIClient.for_connection(connection)
    pipelines = client.get_pipelines()

    cache = {}
    for pipeline in pipelines:
        statuses = pipeline.get('_embedded', {}).get('statuses', [])
        for s in statuses:
            cache[str(s['id'])] = {
                'name': s.get('name', ''),
                'sort': s.get('sort', 0),
                'pipeline_id': str(pipeline.get('id', '')),
                'pipeline_name': pipeline.get('name', ''),
            }

    connection.pipeline_cache = cache
    connection.pipeline_cache_updated_at = timezone.now()
    connection.save(update_fields=['pipeline_cache', 'pipeline_cache_updated_at'])
    return cache


def _stage_name(connection, status_id) -> str:
    entry = connection.pipeline_cache.get(str(status_id))
    if entry:
        return entry['name']
    return {WON_STATUS_ID: 'Closed Won', LOST_STATUS_ID: 'Closed Lost'}.get(status_id, f'Status {status_id}')


def refresh_funnel_counts(connection, force=False) -> dict:
    """
    Count every lead in the tenant's Kommo account by its current stage —
    independent of ad-click matching. Used for the funnel so it's useful
    even before Meta is connected (which is what actually creates the
    PipelineDeal/KommoMatchedLead records the ad-attributed path relies on).
    Cached for an hour unless force=True.
    """
    if not force and connection.funnel_counts_cache and connection.funnel_counts_updated_at:
        age = timezone.now() - connection.funnel_counts_updated_at
        if age < timedelta(hours=1):
            return connection.funnel_counts_cache

    refresh_pipeline_cache(connection)
    client = KommoAPIClient.for_connection(connection)

    counts = {}
    page = 1
    while True:
        leads = client.get_leads(page=page, limit=250)
        if not leads:
            break
        for lead in leads:
            name = _stage_name(connection, lead.get('status_id'))
            counts[name] = counts.get(name, 0) + 1
        if len(leads) < 250:
            break
        page += 1
        if page > 40:  # safety cap — 10,000 leads
            logger.warning(f"Funnel count for {connection.tenant.name} stopped at page cap")
            break

    connection.funnel_counts_cache = counts
    connection.funnel_counts_updated_at = timezone.now()
    connection.save(update_fields=['funnel_counts_cache', 'funnel_counts_updated_at'])
    return counts


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
        lead_id = str(candidate['id'])

        # Edge case: the organic sync may have already claimed this exact
        # Kommo lead (e.g. it was Won before the ad-click match finished).
        # Reassign that record to this deal instead of creating a second,
        # duplicate match for the same lead — avoids double-counting the Sale.
        from .models import KommoMatchedLead
        existing = KommoMatchedLead.objects.filter(
            tenant=tenant, kommo_lead_id=lead_id
        ).exclude(id=matched_lead.id).first()
        if existing:
            existing.pipeline_deal = deal
            existing.save(update_fields=['pipeline_deal'])
            # If it already synced as an unattributed Sale, backfill the
            # ad/campaign attribution now that we know which click caused it.
            if existing.sale_id:
                existing.sale.pipeline_deal = deal
                existing.sale.ad = deal.ad
                existing.sale.campaign = deal.campaign
                if deal.platform in ('facebook', 'instagram'):
                    existing.sale.platform_source = deal.platform
                existing.sale.customer_name = existing.sale.customer_name or deal.customer_name
                existing.sale.customer_phone = existing.sale.customer_phone or deal.customer_phone
                existing.sale.save()
            matched_lead.delete()
            logger.info(f"Kommo lead {lead_id} was already organically synced — reassigned to ad-matched deal {deal.id}")
            return True

        matched_lead.kommo_lead_id = lead_id
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


def _create_sale_from_lead(tenant, lead, connection, deal=None) -> 'Sale':
    """Shared Sale-creation logic for both the ad-matched and unmatched paths."""
    from apps.sales.models import Sale

    amount = lead.get('price') or 0
    closed_at = lead.get('closed_at')
    sale_date = timezone.datetime.fromtimestamp(closed_at).date() if closed_at else timezone.now().date()

    if deal:
        platform_source = deal.platform if deal.platform in ('facebook', 'instagram') else 'other'
        customer_name  = deal.customer_name
        customer_phone = deal.customer_phone
        notes = f"Synced from Kommo lead #{lead.get('id')} (Won, ad-matched)"
        ad, campaign, pipeline_deal = deal.ad, deal.campaign, deal
    else:
        platform_source = 'organic'
        contacts = lead.get('_embedded', {}).get('contacts', [])
        customer_name  = (contacts[0].get('name') or '') if contacts else ''
        customer_phone = ''
        notes = f"Synced from Kommo lead #{lead.get('id')} (Won, no ad-click match)"
        ad, campaign, pipeline_deal = None, None, None

    return Sale.objects.create(
        tenant          = tenant,
        pipeline_deal   = pipeline_deal,
        ad              = ad,
        campaign        = campaign,
        customer_name   = customer_name,
        customer_phone  = customer_phone,
        product_name    = lead.get('name') or 'Kommo deal',
        amount          = amount,
        payment_method  = 'other',
        platform_source = platform_source,
        sale_date       = sale_date,
        is_confirmed    = True,
        notes           = notes,
    )


def sync_lead_status(matched_lead) -> bool:
    """
    For an already-matched lead, refresh its current Kommo stage
    (kommo_status_id/name — whatever that client calls it, e.g. "Qualified
    HOT"). If the stage is Won, also create the Sale. Returns True if a
    Sale was created this call.
    """
    tenant = matched_lead.tenant
    connection = tenant.kommo_connection
    refresh_pipeline_cache(connection)
    client = KommoAPIClient.for_connection(connection)

    lead = client.get_lead(matched_lead.kommo_lead_id)
    matched_lead.raw_lead_data = lead
    matched_lead.last_checked  = timezone.now()

    status_id = lead.get('status_id')
    matched_lead.kommo_status_id   = status_id
    matched_lead.kommo_status_name = _stage_name(connection, status_id)
    matched_lead.kommo_pipeline_id = str(lead.get('pipeline_id', ''))

    if status_id == LOST_STATUS_ID:
        matched_lead.status = 'lost'
        matched_lead.save()
        return False

    if status_id != WON_STATUS_ID:
        matched_lead.save()
        return False

    if matched_lead.sale_id:
        matched_lead.save()
        return False  # already synced

    sale = _create_sale_from_lead(tenant, lead, connection, deal=matched_lead.pipeline_deal)

    matched_lead.sale       = sale
    matched_lead.status     = 'won'
    matched_lead.won_amount = sale.amount
    matched_lead.won_at     = timezone.now()
    matched_lead.save()

    logger.info(f"Kommo won-deal synced as Sale {sale.id} for tenant {tenant.name}")
    return True


def sync_unmatched_won_leads(connection) -> dict:
    """
    Catch any Won Kommo lead that never went through the ad-click matching
    flow at all (no PipelineDeal exists for it — e.g. Meta isn't connected
    yet, or the lead came in organically). Creates a Sale for each one
    found, with no ad/campaign attribution, and a KommoMatchedLead row
    (pipeline_deal=None) so it's never double-processed.
    """
    tenant = connection.tenant
    refresh_pipeline_cache(connection)
    client = KommoAPIClient.for_connection(connection)

    existing_ids = set(
        connection.tenant.kommo_matched_leads.exclude(kommo_lead_id='').values_list('kommo_lead_id', flat=True)
    )

    created = 0
    checked = 0
    page = 1
    while True:
        leads = client.get_leads(page=page, limit=250)
        if not leads:
            break
        for lead in leads:
            if lead.get('status_id') != WON_STATUS_ID:
                continue
            checked += 1
            lead_id = str(lead['id'])
            if lead_id in existing_ids:
                continue  # already handled, either ad-matched or a previous organic sync

            try:
                sale = _create_sale_from_lead(tenant, lead, connection, deal=None)
                from .models import KommoMatchedLead
                KommoMatchedLead.objects.create(
                    tenant=tenant,
                    pipeline_deal=None,
                    kommo_lead_id=lead_id,
                    status='won',
                    match_method='none',
                    kommo_status_id=lead.get('status_id'),
                    kommo_status_name=_stage_name(connection, lead.get('status_id')),
                    kommo_pipeline_id=str(lead.get('pipeline_id', '')),
                    sale=sale,
                    won_amount=sale.amount,
                    won_at=timezone.now(),
                    raw_lead_data=lead,
                    matched_at=timezone.now(),
                    last_checked=timezone.now(),
                )
                existing_ids.add(lead_id)
                created += 1
                logger.info(f"Kommo organic won-lead synced as Sale {sale.id} for tenant {tenant.name}")
            except Exception as e:
                logger.warning(f"Failed to sync unmatched won lead {lead_id} for {tenant.name}: {e}")

        if len(leads) < 250:
            break
        page += 1
        if page > 40:
            break

    return {'checked_won': checked, 'created': created}
