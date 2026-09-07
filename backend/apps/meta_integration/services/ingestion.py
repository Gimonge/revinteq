"""Revinteq v3 — Meta Data Ingestion (idempotent upsert)"""
import logging
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from apps.meta_integration.models import AdAccount, Campaign, Ad, AdSpendRecord
from apps.meta_integration.services.meta_api import MetaGraphClient, MetaAPIError

logger = logging.getLogger(__name__)

OBJECTIVE_MAP = {
    'CONVERSIONS': 'CONVERSIONS', 'MESSAGES': 'MESSAGES',
    'LINK_CLICKS': 'TRAFFIC',     'REACH': 'REACH',
    'BRAND_AWARENESS': 'BRAND_AWARENESS', 'VIDEO_VIEWS': 'VIDEO_VIEWS',
    'LEAD_GENERATION': 'LEAD_GENERATION',
}


class MetaIngestionService:
    def __init__(self, ad_account: AdAccount):
        self.ad_account = ad_account
        self.client     = MetaGraphClient(ad_account.access_token)

    def sync_full(self, days_back: int = 30) -> dict:
        summary = {'account': self.ad_account.meta_account_id,
                   'campaigns': 0, 'ads': 0, 'spend_records': 0, 'errors': []}
        try:
            summary['campaigns']     = self._sync_campaigns()
            summary['ads']           = self._sync_ads()
            summary['spend_records'] = self._sync_spend(days_back)
            self.ad_account.last_synced = timezone.now()
            self.ad_account.save(update_fields=['last_synced'])
        except MetaAPIError as e:
            summary['errors'].append(str(e))
            logger.error(f"Meta sync error for {self.ad_account.meta_account_id}: {e}")
        except Exception as e:
            summary['errors'].append(str(e))
            logger.exception(f"Unexpected sync error: {e}")
        return summary

    def _sync_campaigns(self) -> int:
        count = 0
        for raw in self.client.get_campaigns(self.ad_account.meta_account_id):
            name = raw.get('name', '')
            platform = 'instagram' if 'instagram' in name.lower() or ' ig' in name.lower() else 'facebook'
            Campaign.objects.update_or_create(
                meta_campaign_id=raw['id'],
                defaults={
                    'ad_account': self.ad_account,
                    'name':       name,
                    'status':     raw.get('status', 'ACTIVE'),
                    'objective':  OBJECTIVE_MAP.get(raw.get('objective', ''), 'OTHER'),
                    'platform':   platform,
                    'daily_budget': Decimal(raw['daily_budget']) / 100 if raw.get('daily_budget') else None,
                }
            )
            count += 1
        return count

    def _sync_ads(self) -> int:
        count = 0
        for campaign in Campaign.objects.filter(ad_account=self.ad_account):
            try:
                for raw in self.client.get_ads(campaign.meta_campaign_id):
                    name = raw.get('name', '').lower()
                    fmt  = 'REEL' if 'reel' in name else 'STORY' if 'stor' in name else \
                           'VIDEO' if 'video' in name else 'CAROUSEL' if 'carousel' in name else 'IMAGE'
                    Ad.objects.update_or_create(
                        meta_ad_id=raw['id'],
                        defaults={
                            'campaign':  campaign,
                            'name':      raw.get('name', ''),
                            'status':    raw.get('status', 'ACTIVE'),
                            'ad_format': fmt,
                        }
                    )
                    count += 1
            except MetaAPIError as e:
                logger.warning(f"Ads sync failed for campaign {campaign.meta_campaign_id}: {e}")
        return count

    def _sync_spend(self, days_back: int) -> int:
        today      = date.today()
        date_start = (today - timedelta(days=days_back)).isoformat()
        date_stop  = today.isoformat()
        count      = 0
        for ad in Ad.objects.filter(campaign__ad_account=self.ad_account):
            try:
                for row in self.client.get_ad_insights(ad.meta_ad_id, date_start, date_stop):
                    rec_date = date.fromisoformat(row['date_start'])
                    AdSpendRecord.objects.update_or_create(
                        ad=ad, date=rec_date,
                        defaults={
                            'spend':            Decimal(row.get('spend', '0')),
                            'impressions':      int(row.get('impressions', 0)),
                            # outbound_clicks = intentional clicks on the CTA button
                            # (more accurate than generic 'clicks' which includes all interactions)
                            'clicks':           int((row.get('outbound_clicks') or [{}])[0].get('value', 0) or row.get('clicks', 0)),
                            'dm_conversations': int(row.get('messaging_conversation_started_7d', 0)),
                            'is_partial':       (rec_date == today),
                        }
                    )
                    count += 1
            except MetaAPIError as e:
                logger.warning(f"Insights sync failed for ad {ad.meta_ad_id}: {e}")
        return count
