"""Revinteq v3 — Kommo API Client & OAuth Service"""
import logging
import requests
from datetime import timedelta
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class KommoAPIError(Exception):
    pass


class KommoOAuthService:
    """
    Each tenant registers their OWN integration inside their OWN Kommo
    account (Settings -> Integrations -> Create Integration). Because
    they're the account admin, Kommo shows them the Integration ID,
    Secret Key, AND a ready-made Authorization Code directly in that
    modal — no redirect flow needed at all. The client pastes all three
    into Revinteq once; we exchange the code server-side immediately
    (it expires in 20 minutes) and store the resulting tokens.

    The token exchange still requires a redirect_uri parameter that must
    match what the client entered when creating their integration, even
    though it's never actually visited in this flow — clients are told
    to set it to KOMMO_FIXED_REDIRECT_URI.
    """

    @staticmethod
    def exchange_code_for_token(subdomain: str, code: str, client_id: str, client_secret: str) -> dict:
        url = f"https://{subdomain}/oauth2/access_token"
        r = requests.post(url, json={
            'client_id':     client_id,
            'client_secret': client_secret,
            'grant_type':    'authorization_code',
            'code':          code,
            'redirect_uri':  settings.KOMMO_FIXED_REDIRECT_URI,
        }, timeout=30)
        if r.status_code >= 400:
            raise KommoAPIError(f"Kommo token exchange failed ({r.status_code}): {r.text[:300]}")
        return r.json()

    @staticmethod
    def refresh_access_token(subdomain: str, refresh_token: str, client_id: str, client_secret: str) -> dict:
        url = f"https://{subdomain}/oauth2/access_token"
        r = requests.post(url, json={
            'client_id':     client_id,
            'client_secret': client_secret,
            'grant_type':    'refresh_token',
            'refresh_token': refresh_token,
            'redirect_uri':  settings.KOMMO_FIXED_REDIRECT_URI,
        }, timeout=30)
        if r.status_code >= 400:
            raise KommoAPIError(f"Kommo token refresh failed ({r.status_code}): {r.text[:300]}")
        return r.json()

    @staticmethod
    def compute_token_expiry(expires_in_seconds: int):
        return timezone.now() + timedelta(seconds=expires_in_seconds)


class KommoAPIClient:
    """
    Thin wrapper around a single tenant's Kommo account API.
    Call KommoAPIClient.for_connection(connection) to get an instance with
    a valid (auto-refreshed) access token already applied.
    """

    def __init__(self, subdomain: str, access_token: str):
        self.base_url = subdomain if subdomain.startswith('http') else f"https://{subdomain}"
        self.base_url = self.base_url.rstrip('/')
        self.session  = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}',
            'Content-Type':  'application/json',
        })

    @classmethod
    def for_connection(cls, connection):
        """Build a client for a KommoConnection, refreshing its token first if expired."""
        if connection.is_token_expired:
            from .matching import refresh_connection_token
            refresh_connection_token(connection)
            connection.refresh_from_db()
        return cls(connection.subdomain, connection.access_token)

    def _get(self, path: str, params: dict = None) -> dict:
        url = f"{self.base_url}{path}"
        r = self.session.get(url, params=params or {}, timeout=30)
        if r.status_code == 204:
            return {}
        if r.status_code >= 400:
            raise KommoAPIError(f"Kommo API {path} failed ({r.status_code}): {r.text[:300]}")
        return r.json() if r.text else {}

    def get_leads(self, updated_since: int = None, page: int = 1, limit: int = 250,
                  query: str = None) -> list:
        """
        GET /api/v4/leads
        updated_since: unix timestamp — only leads updated after this time
        query: free-text search (e.g. a phone number)
        """
        params = {'page': page, 'limit': limit, 'with': 'contacts'}
        if updated_since:
            params['filter[updated_at][from]'] = updated_since
        if query:
            params['query'] = query
        data = self._get('/api/v4/leads', params=params)
        return data.get('_embedded', {}).get('leads', [])

    def get_lead(self, lead_id: str) -> dict:
        return self._get(f'/api/v4/leads/{lead_id}', params={'with': 'contacts'})

    def get_contact(self, contact_id: str) -> dict:
        return self._get(f'/api/v4/contacts/{contact_id}')

    def find_leads_by_phone(self, phone: str) -> list:
        """
        Kommo's free-text `query` param searches contact fields including
        phone. Returns the associated leads for any matching contact.
        """
        digits = ''.join(ch for ch in phone if ch.isdigit())
        if not digits:
            return []
        return self.get_leads(query=digits)

    def get_pipelines(self) -> list:
        data = self._get('/api/v4/leads/pipelines')
        return data.get('_embedded', {}).get('pipelines', [])
