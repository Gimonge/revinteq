"""Revinteq v3 — Kommo Integration Views"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.common.views import get_tenant
from .models import KommoConnection
from .services.kommo_api import KommoAPIClient, KommoAPIError

logger = logging.getLogger(__name__)


class KommoConnectManualView(APIView):
    """
    POST /api/v1/kommo/connect/
    Body: { subdomain, long_lived_token }

    Each tenant generates their own Long-lived Token inside their own
    Kommo account (Settings -> Integrations -> their integration -> Keys
    and scopes -> Generate long-lived token) — Kommo's recommended
    approach for a private, single-account integration like this one.
    No OAuth exchange, no redirect, no client secret involved. We verify
    the token actually works before saving it.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tenant = get_tenant(request)
        if not tenant:
            return Response({'error': True, 'message': 'No tenant for this account.'}, status=400)

        subdomain = (request.data.get('subdomain') or '').strip()
        token     = (request.data.get('long_lived_token') or '').strip()

        missing = [f for f, v in [('subdomain', subdomain), ('long_lived_token', token)] if not v]
        if missing:
            return Response({'error': True, 'message': f"Missing: {', '.join(missing)}"}, status=400)

        # Normalize subdomain — accept either "name.kommo.com" or full URL
        if subdomain.startswith('http'):
            subdomain = subdomain.split('//', 1)[-1].rstrip('/')

        client = KommoAPIClient(subdomain, token)
        try:
            client.verify_token()
        except KommoAPIError as e:
            logger.warning(f"Kommo connect failed for {tenant.name}: {e}")
            return Response({'error': True, 'message': f"Couldn't verify token: {e}"}, status=400)

        KommoConnection.objects.update_or_create(
            tenant=tenant,
            defaults={
                'subdomain':    subdomain,
                'access_token': token,
                'sync_enabled': True,
                'last_error':   '',
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
