"""Revinteq v3 — Kommo Integration Views"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.common.views import get_tenant
from .models import KommoConnection
from .services.kommo_api import KommoAPIClient, KommoAPIError

logger = logging.getLogger(__name__)


class KommoFunnelView(APIView):
    """
    GET /api/v1/kommo/funnel/
    Count of every lead in the tenant's Kommo account, per stage — pulled
    from the whole account, independent of ad-click matching (so it's
    useful even before Meta is connected). Sales/revenue attribution is
    unaffected by this — that still only happens for leads matched to a
    real ad click via KommoMatchedLead.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant = get_tenant(request)
        if not tenant:
            return Response({'connected': False, 'stages': []})

        try:
            conn = tenant.kommo_connection
        except KommoConnection.DoesNotExist:
            return Response({'connected': False, 'stages': []})

        from .services.matching import refresh_funnel_counts
        try:
            counts = refresh_funnel_counts(conn)
        except Exception as e:
            logger.warning(f"Funnel fetch failed for {tenant.name}: {e}")
            counts = conn.funnel_counts_cache

        # Order by each stage's real position in the tenant's own pipeline
        ordered = sorted(
            conn.pipeline_cache.values(),
            key=lambda s: (s.get('pipeline_id', ''), s.get('sort', 0))
        )
        seen = set()
        stages = []
        for s in ordered:
            name = s['name']
            if name in seen:
                continue
            seen.add(name)
            stages.append({'name': name, 'count': counts.get(name, 0)})

        # Any stage names on leads that aren't in the current cache
        # (e.g. cache is stale) still get shown, appended at the end
        for name, count in counts.items():
            if name not in seen:
                stages.append({'name': name, 'count': count})

        return Response({
            'connected': True,
            'funnel_updated_at': conn.funnel_counts_updated_at,
            'stages': stages,
        })


class KommoLeadsListView(APIView):
    """
    GET /api/v1/kommo/leads/?page=1&limit=50
    Raw list of every lead in the tenant's Kommo account, with their
    current stage name — independent of ad-click matching, so it's
    useful even before Meta is connected.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant = get_tenant(request)
        if not tenant:
            return Response({'connected': False, 'results': []})

        try:
            conn = tenant.kommo_connection
        except KommoConnection.DoesNotExist:
            return Response({'connected': False, 'results': []})

        from .services.matching import refresh_pipeline_cache, _stage_name
        from .services.kommo_api import KommoAPIClient, KommoAPIError

        refresh_pipeline_cache(conn)
        client = KommoAPIClient.for_connection(conn)

        page  = int(request.query_params.get('page', 1))
        limit = min(int(request.query_params.get('limit', 50)), 250)

        try:
            leads = client.get_leads(page=page, limit=limit)
        except KommoAPIError as e:
            return Response({'connected': True, 'error': str(e), 'results': []}, status=502)

        results = []
        for lead in leads:
            contacts = lead.get('_embedded', {}).get('contacts', [])
            contact_name = contacts[0].get('name') if contacts else ''
            results.append({
                'id':            lead.get('id'),
                'name':          contact_name or lead.get('name') or f"Lead #{lead.get('id')}",
                'price':         lead.get('price') or 0,
                'stage_name':    _stage_name(conn, lead.get('status_id')),
                'created_at':    lead.get('created_at'),
                'updated_at':    lead.get('updated_at'),
            })

        return Response({
            'connected': True,
            'page':      page,
            'results':   results,
        })


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

        connection, _ = KommoConnection.objects.update_or_create(
            tenant=tenant,
            defaults={
                'subdomain':    subdomain,
                'access_token': token,
                'sync_enabled': True,
                'last_error':   '',
            }
        )
        logger.info(f"Kommo connected for {tenant.name} ({subdomain})")

        try:
            from .services.matching import refresh_pipeline_cache, refresh_funnel_counts
            refresh_pipeline_cache(connection, force=True)
            refresh_funnel_counts(connection, force=True)
        except Exception as e:
            logger.warning(f"Could not fetch Kommo pipeline structure for {tenant.name}: {e}")

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
            connection = tenant.kommo_connection
        except KommoConnection.DoesNotExist:
            return Response({'error': True, 'message': 'Kommo is not connected.'}, status=400)

        try:
            from .services.matching import refresh_pipeline_cache, refresh_funnel_counts
            refresh_pipeline_cache(connection, force=True)
            refresh_funnel_counts(connection, force=True)
        except Exception as e:
            logger.warning(f"Pipeline cache refresh failed for {tenant.name}: {e}")

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
