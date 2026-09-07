"""Revinteq v3 — Meta Integration Views"""
import secrets, logging
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated
from apps.tenants.permissions import IsClientOrAdmin, IsAdminOrSuperAdmin
from .models import AdAccount, Campaign, Ad
from .serializers import AdAccountSerializer, CampaignListSerializer, CampaignDetailSerializer
from .services.meta_api import MetaOAuthService, MetaGraphClient, MetaAPIError

logger = logging.getLogger(__name__)


class MetaConnectView(APIView):
    """GET /api/v1/meta/connect/?platform=facebook|instagram"""
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        platform = request.query_params.get('platform', 'facebook')
        state    = secrets.token_urlsafe(32)
        request.session['meta_oauth_state']    = state
        request.session['meta_oauth_platform'] = platform
        oauth_url = MetaOAuthService.get_oauth_url(state_token=state)
        return Response({'oauth_url': oauth_url, 'platform': platform})


class MetaCallbackView(APIView):
    """GET /api/v1/meta/callback/ — Meta OAuth redirect target"""
    permission_classes = []
    authentication_classes = []
    renderer_classes = [JSONRenderer]

    def get(self, request):
        code      = request.query_params.get('code')
        state     = request.query_params.get('state')
        error     = request.query_params.get('error')

        if error:
            return Response({'error': True, 'message': f'Meta declined: {error}'}, status=400)
        from django.core.cache import cache
        oauth_data = cache.get(f'meta_oauth_{state}') if state else None
        if not oauth_data:
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect('https://client.revinteq.com/?meta_error=invalid_state')

        platform  = oauth_data.get('platform', 'facebook')
        tenant_id = oauth_data.get('tenant_id')
        cache.delete(f'meta_oauth_{state}')
        try:
            token_data  = MetaOAuthService.exchange_code_for_token(code)
            short_token = token_data.get('access_token')
            client      = MetaGraphClient(short_token)
            long_data   = client.exchange_for_long_lived_token(short_token)
            long_token  = long_data.get('access_token')
            expires_in  = long_data.get('expires_in', 5183944)
            expiry      = MetaOAuthService.compute_token_expiry(expires_in)

            client       = MetaGraphClient(long_token)
            ad_accounts  = client.get_ad_accounts()

            if not ad_accounts:
                return Response({'error': True, 'message': 'No ad accounts found on this Meta profile.'}, status=400)

            from apps.tenants.models import Tenant
            try:
                tenant = Tenant.objects.get(id=tenant_id)
            except Tenant.DoesNotExist:
                from django.http import HttpResponseRedirect
                return HttpResponseRedirect('https://client.revinteq.com/?meta_error=no_tenant')
            for raw in ad_accounts:
                acct_name = raw.get('name') or raw.get('id') or 'Ad Account'
                AdAccount.objects.update_or_create(
                    meta_account_id=raw['id'],
                    defaults={
                        'tenant':           tenant,
                        'account_name':     acct_name,
                        'platform':         platform or 'facebook',
                        'access_token':     long_token,
                        'token_expires_at': expiry,
                        'currency':         raw.get('currency') or 'KES',
                    }
                )

            # Update tenant connection flags
            if platform == 'facebook':
                tenant.meta_fb_connected = True
            else:
                tenant.meta_ig_connected = True
            tenant.save(update_fields=['meta_fb_connected', 'meta_ig_connected'])

            # Kick off first sync directly (no Celery needed)
            try:
                from .services.meta_sync import MetaSyncService
                MetaSyncService.sync_tenant(tenant)
            except Exception as sync_err:
                logger.warning(f"Initial sync failed: {sync_err}")

            logger.info(f"Meta {platform} connected for {tenant.name}")
            return Response({
                'message':           f'{platform.title()} connected successfully!',
                'ad_accounts_found': len(ad_accounts),
                'token_expires_at':  expiry,
            })

        except MetaAPIError as e:
            return Response({'error': True, 'message': str(e)}, status=502)
        except Exception as e:
            logger.exception(f"Meta callback error: {e}")
            from django.http import HttpResponseRedirect
            import urllib.parse
            return HttpResponseRedirect(f'https://client.revinteq.com/?meta_error={urllib.parse.quote(str(e)[:100])}')


class AdAccountListView(APIView):
    """GET /api/v1/meta/accounts/"""
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def get(self, request):
        accounts = AdAccount.objects.filter(tenant=request.tenant)
        return Response(AdAccountSerializer(accounts, many=True).data)


class MetaSyncView(APIView):
    """
    POST /api/v1/meta/sync/
    Triggers a background sync for the current tenant.
    Returns immediately — sync runs in a background thread.
    Smart: skips if data is fresh (synced within last 5 minutes).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.common.views import get_tenant
        from .models import AdAccount
        from .services.ingestion import MetaIngestionService
        from django.utils import timezone
        from datetime import timedelta
        import threading

        tenant = get_tenant(request)
        if not tenant:
            return Response({'error': True, 'message': 'No tenant found.'}, status=400)

        force = request.data.get('force', False)

        from django.db.models import Q
        accounts = AdAccount.objects.filter(Q(tenant=tenant) | Q(assigned_tenant=tenant))
        if not accounts.exists():
            return Response({'status': 'no_accounts', 'message': 'No ad accounts connected.'})

        # Check freshness — skip if synced within last 5 minutes (unless forced)
        if not force:
            fresh_threshold = timezone.now() - timedelta(minutes=5)
            recently_synced = accounts.filter(last_synced__gte=fresh_threshold).exists()
            if recently_synced:
                return Response({'status': 'fresh', 'message': 'Data is fresh — no sync needed.'})

        # Run sync in background thread so page loads immediately
        def run_sync():
            for account in accounts:
                try:
                    service = MetaIngestionService(account)
                    service.sync_full(days_back=30)
                    account.last_synced = timezone.now()
                    account.save(update_fields=['last_synced'])
                except Exception as e:
                    logger.warning(f"Sync failed for {account.account_name}: {e}")

        thread = threading.Thread(target=run_sync, daemon=True)
        thread.start()

        return Response({
            'status': 'syncing',
            'message': f'Sync started for {accounts.count()} accounts.',
        })


class CampaignListView(APIView):
    """GET /api/v1/meta/campaigns/?platform=facebook&tenant=<id>"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.common.views import get_tenant
        from apps.tenants.models import Tenant

        # Admin can pass ?tenant=<id> to query specific tenant
        tenant_id = request.query_params.get('tenant')
        if tenant_id and (request.user.is_superuser or getattr(request, 'tenant_user', None)):
            try:
                tenant = Tenant.objects.get(id=tenant_id)
            except Tenant.DoesNotExist:
                return Response([])
        else:
            tenant = get_tenant(request)

        if not tenant:
            return Response([])

        from django.db.models import Q
        qs = Campaign.objects.filter(
            Q(ad_account__tenant=tenant) | Q(ad_account__assigned_tenant=tenant)
        ).select_related('ad_account')

        platform = request.query_params.get('platform')
        if platform:
            qs = qs.filter(platform__in=[platform, 'both'])

        return Response(CampaignListSerializer(qs, many=True).data)


class CampaignDetailView(APIView):
    """GET /api/v1/meta/campaigns/<id>/"""
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def get(self, request, campaign_id):
        try:
            c = Campaign.objects.prefetch_related('ads__spend_records').get(
                id=campaign_id, ad_account__tenant=request.tenant
            )
        except Campaign.DoesNotExist:
            return Response({'error': True, 'message': 'Campaign not found.'}, status=404)
        return Response(CampaignDetailSerializer(c).data)


class MetaAuthView(APIView):
    """GET /api/v1/meta/auth/ — redirect to Facebook OAuth"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        import secrets
        from apps.common.views import get_tenant
        from django.http import HttpResponseRedirect

        tenant = get_tenant(request)
        if not tenant:
            return Response({'error': 'No tenant found.'}, status=400)

        state = secrets.token_urlsafe(32)
        # Store state in cache keyed by state token (session unreliable cross-domain)
        from django.core.cache import cache
        cache.set(f'meta_oauth_{state}', {
            'tenant_id': str(tenant.id),
            'platform':  'facebook',
        }, timeout=600)  # 10 minutes

        from .services.meta_api import MetaOAuthService
        oauth_url = MetaOAuthService.get_oauth_url(state)
        return Response({'oauth_url': oauth_url})


class AdPerformanceView(APIView):
    """GET /api/v1/meta/ads/performance/ — ad performance data"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.common.views import get_tenant
        from .models import Ad, Campaign

        tenant = get_tenant(request)
        if not tenant:
            return Response([])

        try:
            from django.db.models import Q
            ads = Ad.objects.filter(
                Q(campaign__ad_account__tenant=tenant) |
                Q(campaign__ad_account__assigned_tenant=tenant)
            ).select_related('campaign', 'campaign__ad_account').order_by('-created_at')

            data = []
            for ad in ads:
                data.append({
                    'id':           str(ad.id),
                    'name':         ad.name,
                    'platform':     getattr(ad.campaign.ad_account, 'platform', 'facebook'),
                    'status':       ad.status,
                    'spend':        float(getattr(ad, 'spend', 0) or 0),
                    'revenue':      float(getattr(ad, 'revenue', 0) or 0),
                    'roi':          float(getattr(ad, 'roi', 0) or 0),
                    'aov':          float(getattr(ad, 'aov', 0) or 0),
                    'sales_count':  int(getattr(ad, 'sales_count', 0) or 0),
                    'conversations':int(getattr(ad, 'conversations', 0) or 0),
                    'campaign_name':ad.campaign.name,
                })
            return Response(data)
        except Exception:
            return Response([])


class AdminAdAccountView(APIView):
    """
    GET  /api/v1/meta/admin/accounts/         — list all ad accounts across all tenants
    POST /api/v1/meta/admin/accounts/<id>/assign/ — assign ad account to a tenant
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Allow superusers and staff
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(pk=request.user.pk)
            if not (user.is_superuser or user.is_staff):
                return Response({'error': 'Admin only.'}, status=403)
        except Exception:
            return Response({'error': 'Admin only.'}, status=403)
        from apps.meta_integration.models import AdAccount
        from apps.tenants.models import Tenant
        accounts = AdAccount.objects.select_related('tenant', 'assigned_tenant').all()
        data = []
        for a in accounts:
            data.append({
                'id':               str(a.id),
                'meta_account_id':  a.meta_account_id,
                'account_name':     a.account_name,
                'platform':         a.platform,
                'currency':         a.currency,
                'owner_tenant_id':  str(a.tenant.id),
                'owner_tenant':     a.tenant.name,
                'assigned_tenant_id': str(a.assigned_tenant.id) if a.assigned_tenant else None,
                'assigned_tenant':    a.assigned_tenant.name if a.assigned_tenant else None,
                'last_synced':      a.last_synced.isoformat() if a.last_synced else None,
            })
        return Response(data)

    def post(self, request, account_id=None):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(pk=request.user.pk)
            if not (user.is_superuser or user.is_staff):
                return Response({'error': 'Admin only.'}, status=403)
        except Exception:
            return Response({'error': 'Admin only.'}, status=403)
        from apps.meta_integration.models import AdAccount
        from apps.tenants.models import Tenant
        try:
            account = AdAccount.objects.get(id=account_id)
        except AdAccount.DoesNotExist:
            return Response({'error': 'Ad account not found.'}, status=404)
        tenant_id = request.data.get('tenant_id')
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id)
                account.assigned_tenant = tenant
            except Tenant.DoesNotExist:
                return Response({'error': 'Tenant not found.'}, status=404)
        else:
            account.assigned_tenant = None
        account.save(update_fields=['assigned_tenant'])

        # Auto-set meta_fb_connected on the assigned tenant
        if account.assigned_tenant:
            if account.platform in ('facebook', 'both'):
                account.assigned_tenant.meta_fb_connected = True
                account.assigned_tenant.save(update_fields=['meta_fb_connected'])
            if account.platform in ('instagram', 'both'):
                account.assigned_tenant.meta_ig_connected = True
                account.assigned_tenant.save(update_fields=['meta_ig_connected'])

            # Trigger a background sync for the newly assigned tenant
            import threading
            from apps.meta_integration.services.ingestion import MetaIngestionService
            def run_sync():
                try:
                    service = MetaIngestionService(account)
                    service.sync_full(days_back=30)
                    from django.utils import timezone as tz
                    account.last_synced = tz.now()
                    account.save(update_fields=['last_synced'])
                except Exception as e:
                    logger.warning(f"Auto-sync after assignment failed: {e}")
            threading.Thread(target=run_sync, daemon=True).start()
        else:
            # When unassigning, check if tenant has any other assigned accounts
            from apps.meta_integration.models import AdAccount as AA
            remaining_fb = AA.objects.filter(
                assigned_tenant=account.assigned_tenant,
                platform__in=['facebook', 'both']
            ).exclude(id=account.id).exists()
            if not remaining_fb:
                # No more assigned fb accounts — but don't disconnect
                # because they may have their own connected account
                pass

        return Response({
            'message': f'Ad account {account.account_name} assigned to {account.assigned_tenant.name if account.assigned_tenant else "none"}',
            'account_id': str(account.id),
            'assigned_tenant': account.assigned_tenant.name if account.assigned_tenant else None,
        })


class ActiveCampaignsView(APIView):
    """GET /api/v1/meta/active-campaigns/ — active campaigns for sale attribution dropdown"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.common.views import get_tenant
        tenant = get_tenant(request)
        if not tenant:
            return Response([])

        # Get campaigns from both owned and assigned ad accounts
        from apps.meta_integration.models import AdAccount, Campaign
        from django.db.models import Q

        accounts = AdAccount.objects.filter(
            Q(tenant=tenant) | Q(assigned_tenant=tenant)
        )
        campaigns = Campaign.objects.filter(
            ad_account__in=accounts,
            status='ACTIVE'
        ).select_related('ad_account').order_by('name')

        return Response([{
            'id':           str(c.id),
            'name':         c.name,
            'platform':     c.platform,
            'account_name': c.ad_account.account_name,
            'spend':        0,
        } for c in campaigns])


class MetaTokenStatusView(APIView):
    """GET /api/v1/meta/token-status/ — token health check"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.common.views import get_tenant
        from django.utils import timezone
        from datetime import timedelta
        from apps.meta_integration.models import AdAccount

        if request.user.is_superuser:
            accounts = AdAccount.objects.select_related('tenant').filter(sync_enabled=True)
        else:
            tenant = get_tenant(request)
            if not tenant:
                return Response([])
            accounts = AdAccount.objects.filter(tenant=tenant, sync_enabled=True)

        warning_threshold = timezone.now() + timedelta(days=7)
        results = []
        for acc in accounts:
            status = 'ok'
            if acc.token_expires_at:
                if acc.token_expires_at <= timezone.now():
                    status = 'expired'
                elif acc.token_expires_at <= warning_threshold:
                    status = 'expiring_soon'
            days_left = None
            if acc.token_expires_at:
                days_left = (acc.token_expires_at - timezone.now()).days
            results.append({
                'account_id':    str(acc.id),
                'account_name':  acc.account_name,
                'tenant_name':   acc.tenant.name,
                'platform':      acc.platform,
                'status':        status,
                'days_left':     days_left,
                'last_synced':   acc.last_synced.isoformat() if acc.last_synced else None,
                'token_expires': acc.token_expires_at.isoformat() if acc.token_expires_at else None,
            })
        return Response(results)


class MetaAccountSelectionView(APIView):
    """
    GET  /api/v1/meta/select-account/ — list available ad accounts
    POST /api/v1/meta/select-account/ — save selected ad account
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.common.views import get_tenant
        from django.core.cache import cache
        tenant = get_tenant(request)
        if not tenant:
            return Response({'error': True, 'message': 'No tenant.'}, status=400)
        data = cache.get(f'meta_accounts_{tenant.id}')
        if not data:
            return Response({'error': True, 'message': 'No pending connection. Please reconnect Facebook.'}, status=400)
        return Response({
            'ad_accounts': [
                {'id': a['id'], 'name': a.get('name', a['id']), 'currency': a.get('currency', 'KES')}
                for a in data['ad_accounts']
            ],
            'platform': data['platform'],
        })

    def post(self, request):
        from apps.common.views import get_tenant
        from django.core.cache import cache
        from django.utils import timezone
        from datetime import datetime
        from apps.meta_integration.models import AdAccount

        tenant = get_tenant(request)
        if not tenant:
            return Response({'error': True, 'message': 'No tenant.'}, status=400)

        selected_id = request.data.get('account_id')
        if not selected_id:
            return Response({'error': True, 'message': 'account_id required.'}, status=400)

        data = cache.get(f'meta_accounts_{tenant.id}')
        if not data:
            return Response({'error': True, 'message': 'Session expired. Please reconnect Facebook.'}, status=400)

        raw = next((a for a in data['ad_accounts'] if a['id'] == selected_id), None)
        if not raw:
            return Response({'error': True, 'message': 'Account not found.'}, status=400)

        platform   = data['platform'] or 'facebook'
        long_token = data['token']
        expiry     = datetime.fromisoformat(data['expiry']) if data.get('expiry') else None
        acct_name  = raw.get('name') or raw.get('id') or 'Ad Account'

        AdAccount.objects.update_or_create(
            meta_account_id=raw['id'],
            defaults={
                'tenant':           tenant,
                'account_name':     acct_name,
                'platform':         platform,
                'access_token':     long_token,
                'token_expires_at': expiry,
                'currency':         raw.get('currency') or 'KES',
            }
        )

        if platform == 'facebook':
            tenant.meta_fb_connected = True
        else:
            tenant.meta_ig_connected = True
        tenant.save(update_fields=['meta_fb_connected', 'meta_ig_connected'])
        cache.delete(f'meta_accounts_{tenant.id}')

        try:
            account = AdAccount.objects.get(meta_account_id=raw['id'], tenant=tenant)
            from apps.meta_integration.services.ingestion import MetaIngestionService
            import threading
            def run_sync():
                try:
                    MetaIngestionService(account).sync_full(days_back=30)
                except Exception as e:
                    logger.warning(f"Initial sync error: {e}")
            threading.Thread(target=run_sync, daemon=True).start()
        except Exception as e:
            logger.warning(f"Sync start error: {e}")

        return Response({'message': f'{platform.title()} connected successfully!', 'account': acct_name})


class AdminAllCampaignsView(APIView):
    """
    GET /api/v1/meta/admin/campaigns/
    Returns all campaigns across all tenants — admin only.
    Cached 5 min. Uses fast dict serialization instead of DRF serializer.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(pk=request.user.pk)
            if not (user.is_superuser or user.is_staff):
                return Response({'error': 'Admin only.'}, status=403)
        except Exception:
            return Response({'error': 'Admin only.'}, status=403)

        from django.core.cache import cache
        from apps.meta_integration.models import Campaign

        cache_key = 'admin_all_campaigns_v2'
        data = cache.get(cache_key)

        if data is None:
            campaigns = Campaign.objects.select_related(
                'ad_account__tenant', 'ad_account__assigned_tenant'
            ).all()

            data = []
            for c in campaigns:
                tenant = c.ad_account.assigned_tenant or c.ad_account.tenant
                # Fast dict — skip expensive computed properties
                data.append({
                    'id':              str(c.id),
                    'meta_campaign_id': c.meta_campaign_id,
                    'name':            c.name,
                    'status':          c.status,
                    'objective':       c.objective or '',
                    'platform':        c.platform,
                    'daily_budget':    float(c.daily_budget) if c.daily_budget else None,
                    'spend':           0,
                    'impressions':     0,
                    'clicks':          0,
                    'conversations':   0,
                    'ctr':             0,
                    'cpm':             0,
                    'cpr':             0,
                    'revenue':         0,
                    'roi':             0,
                    'aov':             0,
                    'last_synced':     c.updated_at.isoformat() if c.updated_at else None,
                    'client_name':     tenant.name,
                    'currency':        tenant.currency or 'KES',
                })
            cache.set(cache_key, data, timeout=300)

        platform = request.query_params.get('platform')
        if platform:
            data = [c for c in data if c['platform'] in (platform, 'both')]

        status_filter = request.query_params.get('status')
        if status_filter:
            data = [c for c in data if c['status'] == status_filter]

        return Response(data)

