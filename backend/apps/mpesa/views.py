"""
Revinteq v3 — M-Pesa Views
C2B Daraja callback endpoints (public — Safaricom POSTs to these).
Transaction management views (authenticated).
"""
import json
import logging
from datetime import datetime
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from apps.tenants.permissions import IsClientOrAdmin, IsAdminOrSuperAdmin, get_tenant_queryset
from .models import MPesaConfig, MPesaTransaction
from .services.matcher import MPesaTransactionMatcher

logger = logging.getLogger(__name__)


# ── Serializers ───────────────────────────────────────────────

class MPesaTransactionSerializer(ModelSerializer):
    status_display = SerializerMethodField()
    payer_name = SerializerMethodField()

    class Meta:
        model = MPesaTransaction
        fields = [
            'id', 'transaction_id', 'transaction_type',
            'amount', 'payer_name', 'bill_ref_number',
            'transaction_time', 'status', 'status_display',
            'matched_sale', 'matched_pipeline_deal',
            'received_at',
        ]

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_payer_name(self, obj):
        return obj.payer_name


class MPesaConfigSerializer(ModelSerializer):
    class Meta:
        model = MPesaConfig
        fields = [
            'id', 'environment', 'shortcode_type',
            'shortcode', 'account_reference',
            'is_active', 'created_at',
        ]
        # consumer_key, consumer_secret, passkey intentionally excluded


# ── Public Daraja Callback Views ──────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class MPesaValidationView(APIView):
    """
    POST /api/v1/mpesa/callback/validation/<tenant_slug>/
    Safaricom calls this FIRST to ask: should we accept this payment?
    We always return Accept. (Validation can be disabled in Daraja portal too.)
    """
    permission_classes = []  # Public — Safaricom calls this

    def post(self, request, tenant_slug):
        logger.info(f"M-Pesa validation received for tenant: {tenant_slug}")
        # Always accept
        return Response({
            "ResultCode": 0,
            "ResultDesc": "Accepted"
        })


@method_decorator(csrf_exempt, name='dispatch')
class MPesaConfirmationView(APIView):
    """
    POST /api/v1/mpesa/callback/confirmation/<tenant_slug>/
    Safaricom calls this when a payment is confirmed.
    We record the transaction and run the matcher.
    """
    permission_classes = []  # Public — Safaricom calls this

    def post(self, request, tenant_slug):
        try:
            from apps.tenants.models import Tenant
            tenant = Tenant.objects.get(slug=tenant_slug)
        except Tenant.DoesNotExist:
            logger.error(f"M-Pesa callback for unknown tenant slug: {tenant_slug}")
            return Response({"ResultCode": 0, "ResultDesc": "Accepted"})

        try:
            data = request.data
            logger.info(f"M-Pesa C2B confirmation for {tenant.name}: {json.dumps(data)}")

            # Parse the callback payload
            transaction_id = data.get('TransID', '')
            amount = data.get('TransAmount', 0)
            msisdn = data.get('MSISDN', '')
            first_name = data.get('FirstName', '')
            middle_name = data.get('MiddleName', '')
            last_name = data.get('LastName', '')
            bill_ref = data.get('BillRefNumber', '')
            shortcode = data.get('BusinessShortCode', '')

            # Parse transaction time: format is YYYYMMDDHHmmss
            trans_time_str = data.get('TransTime', '')
            try:
                transaction_time = datetime.strptime(trans_time_str, '%Y%m%d%H%M%S')
                transaction_time = timezone.make_aware(transaction_time)
            except (ValueError, TypeError):
                transaction_time = timezone.now()

            # Avoid duplicates
            if MPesaTransaction.objects.filter(transaction_id=transaction_id).exists():
                logger.info(f"Duplicate M-Pesa transaction ignored: {transaction_id}")
                return Response({"ResultCode": 0, "ResultDesc": "Accepted"})

            # Create transaction record
            config = MPesaConfig.objects.filter(
                tenant=tenant, shortcode=shortcode
            ).first()

            transaction = MPesaTransaction.objects.create(
                tenant=tenant,
                config=config,
                transaction_id=transaction_id,
                transaction_type='c2b',
                amount=amount,
                msisdn=msisdn,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                bill_ref_number=bill_ref,
                business_shortcode=shortcode,
                transaction_time=transaction_time,
                raw_callback=data,
            )

            # Run matcher asynchronously
            from .tasks import match_mpesa_transaction
            match_mpesa_transaction.delay(str(transaction.id))

        except Exception as e:
            logger.exception(f"Error processing M-Pesa callback: {e}")
            # Always return 0 to Safaricom — never return error codes
            # to avoid Safaricom thinking the payment was rejected

        return Response({"ResultCode": 0, "ResultDesc": "Accepted"})


# ── Authenticated Views ───────────────────────────────────────

class MPesaTransactionListView(APIView):
    """
    GET /api/v1/mpesa/transactions/
    List M-Pesa transactions for the current tenant.
    """
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def get(self, request):
        transactions = MPesaTransaction.objects.filter(
            tenant=request.tenant
        ).select_related('matched_sale', 'matched_pipeline_deal')

        status_filter = request.query_params.get('status')
        if status_filter:
            transactions = transactions.filter(status=status_filter)

        serializer = MPesaTransactionSerializer(transactions[:100], many=True)
        return Response({
            'total': transactions.count(),
            'unmatched': transactions.filter(status='unmatched').count(),
            'results': serializer.data,
        })


class MPesaManualMatchView(APIView):
    """
    POST /api/v1/mpesa/transactions/<id>/match/
    Manually match an unmatched transaction to a pipeline deal.
    """
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def post(self, request, transaction_id):
        try:
            transaction = MPesaTransaction.objects.get(
                id=transaction_id,
                tenant=request.tenant,
                status='unmatched',
            )
        except MPesaTransaction.DoesNotExist:
            return Response(
                {'error': True, 'message': 'Transaction not found or already matched.'},
                status=404
            )

        deal_id = request.data.get('pipeline_deal_id')
        product_name = request.data.get('product_name', 'M-Pesa Payment')

        if not deal_id:
            return Response(
                {'error': True, 'message': 'pipeline_deal_id is required.'},
                status=400
            )

        try:
            from apps.pipeline.models import PipelineDeal
            deal = PipelineDeal.objects.get(id=deal_id, tenant=request.tenant)
        except PipelineDeal.DoesNotExist:
            return Response(
                {'error': True, 'message': 'Pipeline deal not found.'},
                status=404
            )

        # Force the match
        from apps.sales.models import Sale
        sale = Sale.objects.create(
            tenant=request.tenant,
            pipeline_deal=deal,
            ad=deal.ad,
            campaign=deal.campaign,
            product_name=product_name,
            amount=transaction.amount,
            payment_method='mpesa_auto',
            mpesa_reference=transaction.transaction_id,
            platform_source=deal.platform,
            sale_date=transaction.transaction_time.date(),
            is_confirmed=True,
            created_by=request.user,
            notes=f"Manually matched M-Pesa payment. Ref: {transaction.transaction_id}",
        )

        deal.advance_to_stage('won')

        transaction.status = 'matched'
        transaction.matched_sale = sale
        transaction.matched_pipeline_deal = deal
        transaction.matched_at = timezone.now()
        transaction.save()

        return Response({
            'message': 'Transaction matched successfully.',
            'sale_id': str(sale.id),
        })


class MPesaConfigView(APIView):
    """
    GET  /api/v1/admin/mpesa-config/<tenant_id>/  — view config (admin only)
    POST /api/v1/admin/mpesa-config/<tenant_id>/  — create/update config
    """
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def get(self, request, tenant_id):
        try:
            from apps.tenants.models import Tenant
            tenant = Tenant.objects.get(id=tenant_id)
            config = MPesaConfig.objects.get(tenant=tenant)
            return Response(MPesaConfigSerializer(config).data)
        except (Tenant.DoesNotExist, MPesaConfig.DoesNotExist):
            return Response({'configured': False})

    def post(self, request, tenant_id):
        try:
            from apps.tenants.models import Tenant
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return Response({'error': True, 'message': 'Tenant not found.'}, status=404)

        data = request.data
        config, created = MPesaConfig.objects.update_or_create(
            tenant=tenant,
            defaults={
                'environment': data.get('environment', 'sandbox'),
                'shortcode_type': data.get('shortcode_type', 'till'),
                'shortcode': data.get('shortcode', ''),
                'consumer_key': data.get('consumer_key', ''),
                'consumer_secret': data.get('consumer_secret', ''),
                'account_reference': data.get('account_reference', ''),
                'passkey': data.get('passkey', ''),
                'is_active': True,
            }
        )

        # Register C2B URLs with Safaricom
        if data.get('register_urls', False):
            from .tasks import register_mpesa_c2b_urls
            register_mpesa_c2b_urls.delay(str(config.id))

        return Response({
            'message': f'M-Pesa config {"created" if created else "updated"} for {tenant.name}.',
            'config': MPesaConfigSerializer(config).data,
        })


class MPesaConfigTenantView(APIView):
    """
    GET  /api/v1/mpesa/config/?tenant=<id>  — get M-Pesa config for a tenant
    POST /api/v1/mpesa/config/              — create/update M-Pesa config
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.common.views import get_tenant
        from .models import MPesaConfig

        tenant_id = request.query_params.get('tenant')
        if tenant_id:
            try:
                from apps.tenants.models import Tenant
                tenant = Tenant.objects.get(id=tenant_id)
            except Exception:
                return Response(None)
        else:
            tenant = get_tenant(request)

        if not tenant:
            return Response(None)

        try:
            config = MPesaConfig.objects.get(tenant=tenant)
            return Response({
                'id':               str(config.id),
                'tenant':           str(config.tenant_id),
                'environment':      config.environment,
                'shortcode_type':   config.shortcode_type,
                'shortcode':        config.shortcode or '',
                'consumer_key':     '••••••••••••••••••••' if config.consumer_key else '',
                'consumer_secret':  '••••••••••••••••••••' if config.consumer_secret else '',
                'passkey':          '••••••••••••••••••••' if getattr(config, 'passkey', '') else '',
                'is_active':        config.is_active,
                'c2b_registered':   getattr(config, 'c2b_registered', False),
            })
        except Exception:
            return Response(None)

    def post(self, request):
        from apps.common.views import get_tenant
        from .models import MPesaConfig

        tenant_id = request.data.get('tenant')
        if tenant_id:
            try:
                from apps.tenants.models import Tenant
                tenant = Tenant.objects.get(id=tenant_id)
            except Exception:
                return Response({'error': 'Tenant not found'}, status=404)
        else:
            tenant = get_tenant(request)

        if not tenant:
            return Response({'error': 'No tenant'}, status=400)

        config, _ = MPesaConfig.objects.get_or_create(tenant=tenant)
        fields = ['environment', 'shortcode_type', 'shortcode']
        for f in fields:
            if f in request.data:
                setattr(config, f, request.data[f])

        # Only update secrets if provided (not masked)
        for secret_field in ['consumer_key', 'consumer_secret', 'passkey']:
            val = request.data.get(secret_field, '')
            if val and '•' not in val:
                setattr(config, secret_field, val)

        config.save()
        return Response({'message': 'M-Pesa config saved successfully.'})
