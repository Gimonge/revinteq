"""Revinteq v3 — Kommo API Client (Long-lived Token)"""
import logging
import requests

logger = logging.getLogger(__name__)


class KommoAPIError(Exception):
    pass


class KommoAPIClient:
    """
    Thin wrapper around a single tenant's Kommo account API, authenticated
    with a Long-lived Token — Kommo's recommended approach for private,
    single-account integrations. No OAuth exchange, no refresh_token; the
    tenant generates the token themselves and it's used directly as a
    Bearer token until they replace it (it has no programmatic refresh).
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
        """Build a client for a KommoConnection."""
        return cls(connection.subdomain, connection.access_token)

    def _get(self, path: str, params: dict = None) -> dict:
        url = f"{self.base_url}{path}"
        r = self.session.get(url, params=params or {}, timeout=30)
        if r.status_code == 204:
            return {}
        if r.status_code >= 400:
            raise KommoAPIError(f"Kommo API {path} failed ({r.status_code}): {r.text[:300]}")
        return r.json() if r.text else {}

    def verify_token(self) -> dict:
        """Confirm the token actually works by fetching account info."""
        return self._get('/api/v4/account')

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
