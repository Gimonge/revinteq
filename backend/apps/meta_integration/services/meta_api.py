"""Revinteq v3 — Meta Graph API Client"""
import base64, logging, requests
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

BASE_URL = f"https://graph.facebook.com/{getattr(settings, 'META_GRAPH_API_VERSION', 'v20.0')}"


class MetaGraphClient:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.session = requests.Session()
        self.session.params = {'access_token': access_token}

    def _get(self, endpoint: str, params: dict = None) -> dict:
        url = f"{BASE_URL}/{endpoint}"
        try:
            r = self.session.get(url, params=params or {}, timeout=30)
            r.raise_for_status()
            data = r.json()
            if 'error' in data:
                raise MetaAPIError(data['error'].get('message', 'Unknown Meta API error'))
            return data
        except requests.exceptions.Timeout:
            raise MetaAPIError("Meta API request timed out")
        except requests.exceptions.ConnectionError:
            raise MetaAPIError("Cannot connect to Meta API")
        except requests.exceptions.HTTPError as e:
            raise MetaAPIError(f"Meta API HTTP {r.status_code}: {e}")

    def get_ad_accounts(self) -> list:
        data = self._get('me/adaccounts', params={'fields': 'id,name,currency,account_status'})
        return data.get('data', [])

    def get_campaigns(self, ad_account_id: str) -> list:
        act = ad_account_id if ad_account_id.startswith('act_') else f'act_{ad_account_id}'
        data = self._get(f'{act}/campaigns', params={
            'fields': 'id,name,status,objective,daily_budget', 'limit': 200,
        })
        return data.get('data', [])

    def get_ads(self, campaign_id: str) -> list:
        data = self._get(f'{campaign_id}/ads', params={
            'fields': 'id,name,status', 'limit': 200,
        })
        return data.get('data', [])

    def get_ad_insights(self, ad_id: str, date_start: str, date_stop: str) -> list:
        data = self._get(f'{ad_id}/insights', params={
            'fields': 'spend,impressions,clicks,messaging_conversation_started_7d,date_start',
            'time_increment': 1,
            'time_range': f'{{"since":"{date_start}","until":"{date_stop}"}}',
            'level': 'ad',
        })
        return data.get('data', [])

    def exchange_for_long_lived_token(self, short_token: str) -> dict:
        r = requests.get(f"{BASE_URL}/oauth/access_token", params={
            'grant_type': 'fb_exchange_token',
            'client_id': settings.META_APP_ID,
            'client_secret': settings.META_APP_SECRET,
            'fb_exchange_token': short_token,
        }, timeout=30)
        r.raise_for_status()
        return r.json()


class MetaOAuthService:
    @staticmethod
    def get_oauth_url(state_token: str) -> str:
        from urllib.parse import urlencode
        params = {
            'client_id':     settings.META_APP_ID,
            'redirect_uri':  settings.META_REDIRECT_URI,
            'scope':         settings.META_SCOPES,
            'response_type': 'code',
            'state':         state_token,
        }
        return f"https://www.facebook.com/v20.0/dialog/oauth?{urlencode(params)}"

    @staticmethod
    def exchange_code_for_token(code: str) -> dict:
        r = requests.get(f"{BASE_URL}/oauth/access_token", params={
            'client_id':     settings.META_APP_ID,
            'client_secret': settings.META_APP_SECRET,
            'redirect_uri':  settings.META_REDIRECT_URI,
            'code':          code,
        }, timeout=30)
        r.raise_for_status()
        return r.json()

    @staticmethod
    def compute_token_expiry(expires_in_seconds: int):
        return timezone.now() + timedelta(seconds=expires_in_seconds)


class MetaAPIError(Exception):
    pass
