"""Revinteq v3 — Kommo Integration Views"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.common.views import get_tenant
from .models import KommoConnection
from .services.kommo_api import KommoOAuthService, KommoAPIError

logger = logging.getLogger(__name__)


class KommoConnectManualView(APIView):
    """
    POST /api/v1/kommo/connect/
    Body: { subdomain, client_id, client_secret, auth_code }

    Each tenant registers their own integration inside their own Kommo
    account and pastes the Integration ID, Secret Key, and the
    ready-made Authorization Code Kommo shows them in that same modal
    (no redirect needed). We exchange that code immediately — it
    expires in 20 minutes — and store the resulting tokens.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tenant = get_tenant(request)
        if not tenant:
            return Response({'error': True, 'message': 'No tenant for this account.'}, status=400)

        subdomain     = (request.data.get('subdomain') or '').strip()
        client_id     = (request.data.get('client_id') or '').strip()
        client_secret = (request.data.get('client_secret') or '').strip()
        auth_code     = (request.data.get('auth_code') or '').strip()

        missing = [f for f, v in [('subdomain', subdomain), ('client_id', client_id),
                                    ('client_secret', client_secret), ('auth_code', auth_code)] if not v]
        if missing:
            return Response({'error': True, 'message': f"Missing: {', '.join(missing)}"}, status=400)

        # Normalize subdomain — accept either "name.kommo.com" or full URL
        if subdomain.startswith('http'):
            subdomain = subdomain.split('//', 1)[-1].rstrip('/')

        try:
            token_data = KommoOAuthService.exchange_code_for_token(
                subdomain, auth_code, client_id, client_secret
            )
        except KommoAPIError as e:
            logger.warning(f"Kommo connect failed for {tenant.name}: {e}")
            return Response({'error': True, 'message': str(e)}, status=400)

        expiry = KommoOAuthService.compute_token_expiry(token_data.get('expires_in', 86400))

        KommoConnection.objects.update_or_create(
            tenant=tenant,
            defaults={
                'subdomain':        subdomain,
                'client_id':        client_id,
                'client_secret':    client_secret,
                'access_token':     token_data['access_token'],
                'refresh_token':    token_data['refresh_token'],
                'token_expires_at': expiry,
                'sync_enabled':     True,
                'last_error':       '',
            }
        )
        logger.info(f"Kommo connected for {tenant.name} ({subdomain})")
        return Response({'message': 'Kommo connected successfully!', 'subdomain': subdomain})


class KommoConnectionStatusView(APIView):
    """GET /api/v1/kommo/status/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant = get_tenant(request)
        if not tenant:
            return Response({'connected': False})

        try:
            conn = tenant.kommo_connection
        except KommoConnection.DoesNotExist:
            return Response({'connected': False})

        return Response({
            'connected':    True,
            'subdomain':    conn.subdomain,
            'sync_enabled': conn.sync_enabled,
            'last_synced':  conn.last_synced,
            'last_error':   conn.last_error,
        })


class KommoSyncView(APIView):
    """POST /api/v1/kommo/sync/ — manually trigger a sync check for this tenant."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tenant = get_tenant(request)
        if not tenant:
            return Response({'error': True, 'message': 'No tenant for this account.'}, status=400)

        try:
            tenant.kommo_connection
        except KommoConnection.DoesNotExist:
            return Response({'error': True, 'message': 'Kommo is not connected.'}, status=400)

        from .tasks import sync_matched_leads_for_tenant
        sync_matched_leads_for_tenant.delay(str(tenant.id))
        return Response({'message': 'Sync started.'})


class KommoDisconnectView(APIView):
    """POST /api/v1/kommo/disconnect/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tenant = get_tenant(request)
        if not tenant:
            return Response({'error': True, 'message': 'No tenant for this account.'}, status=400)

        KommoConnection.objects.filter(tenant=tenant).delete()
        return Response({'message': 'Kommo disconnected.'})
