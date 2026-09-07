"""
Revinteq v3 — External API Views
Third-party systems (POS, e-commerce) use these endpoints with API keys.
Authentication: Authorization: Api-Key rvq_live_XXXXXXXX
"""
import logging
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ExternalAPIKey, WebhookEndpoint, WebhookDelivery

logger = logging.getLogger(__name__)


# ── API Key Authentication (defined in authentication.py) ─────
from .authentication import APIKeyAuthentication  # noqa: F401 re-exported


class HasAPIPermission(IsAuthenticated):
    """Check that the API key has the required permission."""

    required_permission = None

    def has_permission(self, request, view):
        if not hasattr(request, 'api_key'):
            return False
        if self.required_permission:
            return getattr(request.api_key, self.required_permission, False)
        return True


# ── External API Views ────────────────────────────────────────

class ExternalSaleCreateView(APIView):
    """
    POST /api/external/v1/sales/
    POS system or website logs a sale directly into Revinteq.

    Request body:
    {
      "product_name": "Blue Dress Size M",
      "amount": 2400,
      "payment_method": "mpesa_manual",
      "payment_reference": "QK47XY8Z21",
      "platform_source": "organic",
      "sale_date": "2026-04-07",
      "notes": "POS terminal sale"
    }
    """
    authentication_classes = [APIKeyAuthentication]

    def post(self, request):
        if not request.api_key.can_create_sales:
            return Response(
                {'error': True, 'message': 'This API key does not have permission to create sales.'},
                status=status.HTTP_403_FORBIDDEN
            )

        from apps.sales.serializers import SaleSerializer

        # Inject tenant into request context
        serializer = SaleSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        sale = serializer.save()

        logger.info(
            f"External API sale created: "
            f"{request.tenant.name} | KES {sale.amount} | "
            f"Key: {request.api_key.name}"
        )

        dispatch_webhook.delay(
            str(request.tenant.id), 'sale.created',
            {
                'sale_id': str(sale.id),
                'amount': float(sale.amount),
                'source': 'external_api',
                'api_key_name': request.api_key.name,
            }
        )

        return Response({
            'success': True,
            'sale_id': str(sale.id),
            'message': 'Sale logged successfully.',
            'amount': float(sale.amount),
        }, status=status.HTTP_201_CREATED)


class ExternalSaleListView(APIView):
    """
    GET /api/external/v1/sales/
    External system reads recent sales.
    """
    authentication_classes = [APIKeyAuthentication]

    def get(self, request):
        if not request.api_key.can_read_sales:
            return Response(
                {'error': True, 'message': 'This API key does not have read permission.'},
                status=status.HTTP_403_FORBIDDEN
            )

        from apps.sales.models import Sale
        from apps.sales.serializers import SaleListSerializer

        sales = Sale.objects.filter(
            tenant=request.tenant
        ).order_by('-sale_date')[:100]

        return Response({
            'count': sales.count(),
            'results': SaleListSerializer(sales, many=True).data,
        })


class ExternalPipelineCreateView(APIView):
    """
    POST /api/external/v1/pipeline/
    External system (e.g. website form) creates a new pipeline deal.
    """
    authentication_classes = [APIKeyAuthentication]

    def post(self, request):
        if not request.api_key.can_create_pipeline_deals:
            return Response(
                {'error': True, 'message': 'This API key cannot create pipeline deals.'},
                status=status.HTTP_403_FORBIDDEN
            )

        from apps.pipeline.models import PipelineDeal

        data = request.data
        deal = PipelineDeal.objects.create(
            tenant=request.tenant,
            customer_name=data.get('customer_name', ''),
            customer_phone=data.get('customer_phone', ''),
            platform=data.get('platform', 'organic'),
            source='manual',
            stage='new_click',
            new_click_at=timezone.now(),
            estimated_value=data.get('estimated_value'),
            notes=data.get('notes', f"Created via External API ({request.api_key.name})"),
            velocity='hot',
        )

        dispatch_webhook.delay(
            str(request.tenant.id), 'pipeline.new_click',
            {'deal_id': str(deal.id), 'source': 'external_api'}
        )

        return Response({
            'success': True,
            'deal_id': str(deal.id),
            'message': 'Pipeline deal created.',
        }, status=status.HTTP_201_CREATED)


class ExternalMetricsSummaryView(APIView):
    """
    GET /api/external/v1/metrics/
    External system reads KPI summary.
    """
    authentication_classes = [APIKeyAuthentication]

    def get(self, request):
        if not request.api_key.can_read_metrics:
            return Response(
                {'error': True, 'message': 'This API key does not have metrics permission.'},
                status=status.HTTP_403_FORBIDDEN
            )

        from apps.metrics.models import MetricSnapshot
        from datetime import date

        month_start = date.today().replace(day=1)
        try:
            snapshot = MetricSnapshot.objects.get(
                tenant=request.tenant,
                period_type='month',
                period_start=month_start,
            )
            return Response({
                'total_revenue': snapshot.total_revenue,
                'total_sales': snapshot.total_sales,
                'total_spend': snapshot.total_spend,
                'roi': snapshot.roi,
                'avg_order_value': snapshot.avg_order_value,
                'conversion_rate': snapshot.conversion_rate,
                'period_start': snapshot.period_start,
                'period_end': snapshot.period_end,
            })
        except MetricSnapshot.DoesNotExist:
            return Response({'message': 'No metrics available yet for this month.'})


# ── Admin: API Key Management ─────────────────────────────────

class APIKeyListCreateView(APIView):
    """
    GET  /api/v1/admin/api-keys/<tenant_id>/  — list keys
    POST /api/v1/admin/api-keys/<tenant_id>/  — create key
    Admin only.
    """
    from apps.tenants.permissions import IsAdminOrSuperAdmin
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request, tenant_id):
        keys = ExternalAPIKey.objects.filter(tenant_id=tenant_id)
        return Response([{
            'id': str(k.id),
            'name': k.name,
            'key': k.key,
            'is_active': k.is_active,
            'can_create_sales': k.can_create_sales,
            'can_create_pipeline_deals': k.can_create_pipeline_deals,
            'can_read_sales': k.can_read_sales,
            'can_read_metrics': k.can_read_metrics,
            'last_used_at': k.last_used_at,
            'created_at': k.created_at,
            'notes': k.notes,
        } for k in keys])

    def post(self, request, tenant_id):
        from apps.tenants.models import Tenant
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return Response({'error': True, 'message': 'Tenant not found.'}, status=404)

        data = request.data
        key = ExternalAPIKey.objects.create(
            tenant=tenant,
            name=data.get('name', 'API Key'),
            can_create_sales=data.get('can_create_sales', True),
            can_create_pipeline_deals=data.get('can_create_pipeline_deals', True),
            can_read_sales=data.get('can_read_sales', True),
            can_read_metrics=data.get('can_read_metrics', False),
            notes=data.get('notes', ''),
            created_by=request.user,
        )

        logger.info(f"API key created for {tenant.name}: {key.name} by {request.user.email}")

        return Response({
            'message': f'API key created for {tenant.name}.',
            'id': str(key.id),
            'name': key.name,
            'key': key.key,  # Shown once at creation
        }, status=status.HTTP_201_CREATED)


class APIKeyRevokeView(APIView):
    """POST /api/v1/admin/api-keys/<key_id>/revoke/"""
    from apps.tenants.permissions import IsAdminOrSuperAdmin
    permission_classes = [IsAdminOrSuperAdmin]

    def post(self, request, key_id):
        try:
            key = ExternalAPIKey.objects.get(id=key_id)
            key.is_active = False
            key.save(update_fields=['is_active'])
            return Response({'message': f'API key "{key.name}" revoked.'})
        except ExternalAPIKey.DoesNotExist:
            return Response({'error': True, 'message': 'Key not found.'}, status=404)



class AdminAPIKeyListView(APIView):
    """
    GET  /api/external/api-keys/       — list all API keys (admin)
    POST /api/external/api-keys/       — create a new API key
    PATCH /api/external/api-keys/<id>/ — update (revoke) a key
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.external_api.models import ExternalAPIKey
        from apps.tenants.models import Tenant
        keys = ExternalAPIKey.objects.select_related('tenant').all().order_by('-created_at')
        data = []
        for k in keys:
            data.append({
                'id':              str(k.id),
                'tenant_id':       str(k.tenant_id),
                'tenant_name':     k.tenant.name,
                'name':            k.name,
                'key':             k.key,
                'is_active':       k.is_active,
                'can_create_sales': k.can_create_sales,
                'can_read_metrics': k.can_read_metrics,
                'last_used_at':    k.last_used_at.isoformat() if k.last_used_at else None,
                'created_at':      k.created_at.isoformat(),
            })
        return Response(data)

    def post(self, request):
        import shortuuid
        from apps.external_api.models import ExternalAPIKey
        from apps.tenants.models import Tenant

        tenant_id = request.data.get('tenant_id')
        name      = request.data.get('name', '')
        if not tenant_id or not name:
            return Response({'error': 'tenant_id and name are required.'}, status=400)
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return Response({'error': 'Tenant not found.'}, status=404)

        key_value = f"rvq_live_{shortuuid.ShortUUID().random(length=20)}"
        key = ExternalAPIKey.objects.create(
            tenant=tenant,
            name=name,
            key=key_value,
            can_create_sales=request.data.get('can_create_sales', True),
            can_read_metrics=request.data.get('can_read_metrics', False),
        )
        return Response({
            'id':              str(key.id),
            'tenant_id':       str(key.tenant_id),
            'tenant_name':     tenant.name,
            'name':            key.name,
            'key':             key.key,
            'is_active':       key.is_active,
            'can_create_sales': key.can_create_sales,
            'can_read_metrics': key.can_read_metrics,
            'last_used_at':    None,
            'created_at':      key.created_at.isoformat(),
        }, status=201)

    def patch(self, request, key_id=None):
        from apps.external_api.models import ExternalAPIKey
        if not key_id:
            return Response({'error': 'key_id required'}, status=400)
        try:
            key = ExternalAPIKey.objects.get(id=key_id)
        except ExternalAPIKey.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        if 'is_active' in request.data:
            key.is_active = request.data['is_active']
        key.save()
        return Response({'id': str(key.id), 'is_active': key.is_active})
