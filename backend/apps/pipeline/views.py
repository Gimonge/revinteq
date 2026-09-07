"""
Revinteq v3 — Pipeline Views
Simplified journey: New Click → Won or Lost (middle stages optional).
Board view groups deals by stage with totals per column.
"""
from decimal import Decimal
from django.db.models import Sum, Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.common.views import get_tenant
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import (
    ModelSerializer, CharField, SerializerMethodField,
    DecimalField, FloatField, IntegerField, BooleanField, Serializer,
    ChoiceField, UUIDField
)
from apps.tenants.permissions import IsClientOrAdmin
from .models import PipelineDeal, StageTransitionLog


class PipelineDealSerializer(ModelSerializer):
    stage_display = CharField(source='get_stage_display', read_only=True)
    platform_display = CharField(source='get_platform_display', read_only=True)
    velocity_display = CharField(source='get_velocity_display', read_only=True)
    stage_color = CharField(read_only=True)
    total_velocity_hours = FloatField(read_only=True, allow_null=True)
    is_stale = BooleanField(read_only=True)
    ad_name = CharField(source='ad.name', read_only=True, allow_null=True)
    campaign_name = CharField(source='campaign.name', read_only=True, allow_null=True)
    has_sale = SerializerMethodField()

    class Meta:
        model = PipelineDeal
        fields = [
            'id', 'customer_name', 'customer_phone',
            'platform', 'platform_display',
            'stage', 'stage_display', 'stage_color',
            'velocity', 'velocity_display', 'is_stale',
            'estimated_value', 'notes', 'lost_reason',
            'ad_name', 'campaign_name',
            'new_click_at', 'contacted_at', 'interested_at',
            'negotiating_at', 'won_at', 'lost_at',
            'days_in_current_stage',
            'total_velocity_hours',
            'source', 'whatsapp_message_id',
            'has_sale', 'created_at',
        ]
        read_only_fields = ['id', 'new_click_at', 'days_in_current_stage', 'created_at']

    def get_has_sale(self, obj):
        return hasattr(obj, 'sale') and obj.sale is not None


class WonLostSerializer(Serializer):
    """Input for direct Won or Lost action."""
    action = ChoiceField(choices=['won', 'lost'])
    lost_reason = CharField(required=False, allow_blank=True, default='')
    notes = CharField(required=False, allow_blank=True, default='')
    # When marking Won — optionally log sale details inline
    log_sale = BooleanField(required=False, default=False)
    product_name = CharField(required=False, allow_blank=True, default='')
    amount = DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    payment_method = CharField(required=False, allow_blank=True, default='cash')
    payment_reference = CharField(required=False, allow_blank=True, default='')


class PipelineBoardView(APIView):
    """
    GET /api/v1/pipeline/board/
    Kanban board — all deals grouped by stage with column totals.
    """
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def get(self, request):
        platform = request.query_params.get('platform')

        deals_qs = PipelineDeal.objects.filter(
            tenant=get_tenant(request)
        ).select_related('ad', 'campaign').order_by('-created_at')

        if platform:
            deals_qs = deals_qs.filter(platform=platform)

        board = {}
        for stage_code, stage_label in PipelineDeal.STAGE_CHOICES:
            stage_deals = deals_qs.filter(stage=stage_code)
            agg = stage_deals.aggregate(total_value=Sum('estimated_value'))
            board[stage_code] = {
                'label': stage_label,
                'count': stage_deals.count(),
                'total_value': agg['total_value'] or Decimal('0'),
                'deals': PipelineDealSerializer(stage_deals, many=True).data,
            }

        # Board-level totals
        open_deals = deals_qs.filter(
            stage__in=['new_click', 'contacted', 'interested', 'negotiating']
        )
        board['_totals'] = {
            'total_open_deals': open_deals.count(),
            'total_pipeline_value': open_deals.aggregate(
                v=Sum('estimated_value')
            )['v'] or Decimal('0'),
            'total_won': deals_qs.filter(stage='won').count(),
            'total_lost': deals_qs.filter(stage='lost').count(),
        }

        return Response(board)


class PipelineDealListCreateView(APIView):
    """
    GET  /api/v1/pipeline/deals/  — list deals with filters
    POST /api/v1/pipeline/deals/  — manually create a deal
    """
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def get(self, request):
        deals = PipelineDeal.objects.filter(
            tenant=get_tenant(request)
        ).select_related('ad', 'campaign').order_by('-created_at')

        if request.query_params.get('stage'):
            deals = deals.filter(stage=request.query_params['stage'])
        if request.query_params.get('platform'):
            deals = deals.filter(platform=request.query_params['platform'])
        if request.query_params.get('velocity'):
            deals = deals.filter(velocity=request.query_params['velocity'])
        if request.query_params.get('stale'):
            deals = deals.filter(days_in_current_stage__gte=3)

        # Totals
        totals = deals.aggregate(
            total_deals=Count('id'),
            total_estimated_value=Sum('estimated_value'),
            open_deals=Count('id', filter=Q(
                stage__in=['new_click','contacted','interested','negotiating']
            )),
            won_deals=Count('id', filter=Q(stage='won')),
            lost_deals=Count('id', filter=Q(stage='lost')),
        )

        return Response({
            'totals': {k: (v or 0) for k, v in totals.items()},
            'results': PipelineDealSerializer(deals, many=True).data,
        })

    def post(self, request):
        serializer = PipelineDealSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deal = serializer.save(
            tenant=get_tenant(request),
            stage='new_click',
            new_click_at=timezone.now(),
            source='manual',
        )
        return Response(
            PipelineDealSerializer(deal).data,
            status=status.HTTP_201_CREATED
        )


class PipelineDealDetailView(APIView):
    """
    GET   /api/v1/pipeline/deals/<id>/ — retrieve a single deal
    PATCH /api/v1/pipeline/deals/<id>/ — update stage, velocity, notes etc.
    """
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def _get_deal(self, deal_id, tenant):
        try:
            return PipelineDeal.objects.get(id=deal_id, tenant=tenant)
        except PipelineDeal.DoesNotExist:
            return None

    def get(self, request, deal_id):
        tenant = get_tenant(request)
        deal = self._get_deal(deal_id, tenant)
        if not deal:
            return Response({'error': 'Not found'}, status=404)
        return Response(PipelineDealSerializer(deal).data)

    def delete(self, request, deal_id):
        from apps.common.views import get_tenant
        try:
            deal = PipelineDeal.objects.get(id=deal_id, tenant=get_tenant(request))
            deal.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PipelineDeal.DoesNotExist:
            return Response({'error': 'Deal not found.'}, status=404)

    def patch(self, request, deal_id):
        tenant = get_tenant(request)
        deal = self._get_deal(deal_id, tenant)
        if not deal:
            return Response({'error': 'Not found'}, status=404)

        allowed = ['stage', 'velocity', 'notes', 'customer_name',
                   'customer_phone', 'estimated_value', 'mpesa_reference',
                   'expected_close_date']
        for field in allowed:
            if field in request.data:
                setattr(deal, field, request.data[field])
        deal.save()
        return Response(PipelineDealSerializer(deal).data)


class PipelineDealActionView(APIView):
    """
    POST /api/v1/pipeline/deals/<id>/action/

    Primary action — directly mark Won or Lost.
    Middle stages still available via /advance/ endpoint.

    If log_sale=true and action=won, creates a Sale record inline.
    """
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def post(self, request, deal_id):
        try:
            deal = PipelineDeal.objects.get(
                id=deal_id, tenant=get_tenant(request)
            )
        except PipelineDeal.DoesNotExist:
            return Response(
                {'error': True, 'message': 'Deal not found.'}, status=404
            )

        serializer = WonLostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        action = data['action']

        if action == 'won':
            deal.mark_won(notes=data.get('notes', ''))
        else:
            deal.mark_lost(
                reason=data.get('lost_reason', ''),
                notes=data.get('notes', '')
            )

        # Log transition
        StageTransitionLog.objects.create(
            deal=deal,
            from_stage=deal.stage,
            to_stage=action,
            transitioned_by=request.user,
            source='manual',
            notes=data.get('notes', ''),
        )

        # Optionally log sale inline when marking Won
        sale = None
        if action == 'won' and data.get('log_sale') and data.get('amount'):
            from apps.sales.models import Sale
            from datetime import date
            sale = Sale.objects.create(
                tenant=get_tenant(request),
                pipeline_deal=deal,
                ad=deal.ad,
                campaign=deal.campaign,
                product_name=data.get('product_name') or 'Sale',
                amount=data['amount'],
                payment_method=data.get('payment_method', 'cash'),
                payment_reference=data.get('payment_reference', ''),
                platform_source=deal.platform,
                sale_date=date.today(),
                is_confirmed=True,
                created_by=request.user,
            )

        # Fire webhooks
        from apps.external_api.tasks import dispatch_webhook
        dispatch_webhook.delay(
            str(get_tenant(request).id),
            f'pipeline.{action}',
            {'deal_id': str(deal.id), 'platform': deal.platform}
        )

        response_data = PipelineDealSerializer(deal).data
        response_data['action_taken'] = action

        if sale:
            response_data['sale_logged'] = True
            response_data['sale_id'] = str(sale.id)

        if action == 'won' and not data.get('log_sale'):
            response_data['prompt_sale_log'] = True
            response_data['message'] = (
                'Deal marked as Won! Log the sale now to update your revenue metrics.'
            )

        return Response(response_data)


class PipelineDealAdvanceView(APIView):
    """
    POST /api/v1/pipeline/deals/<id>/advance/
    Optional: move through middle stages (Contacted → Interested → Negotiating).
    """
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def post(self, request, deal_id):
        try:
            deal = PipelineDeal.objects.get(id=deal_id, tenant=get_tenant(request))
        except PipelineDeal.DoesNotExist:
            return Response({'error': True, 'message': 'Deal not found.'}, status=404)

        new_stage = request.data.get('stage')
        notes = request.data.get('notes', '')

        if not new_stage:
            return Response(
                {'error': True, 'message': 'stage is required.'}, status=400
            )

        old_stage = deal.stage
        deal.advance_to_stage(new_stage, notes=notes)

        StageTransitionLog.objects.create(
            deal=deal,
            from_stage=old_stage,
            to_stage=new_stage,
            transitioned_by=request.user,
            source='manual',
            notes=notes,
        )

        return Response(PipelineDealSerializer(deal).data)


class PipelineSummaryView(APIView):
    """GET /api/v1/pipeline/summary/ — board KPIs."""
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def get(self, request):
        all_deals = PipelineDeal.objects.filter(tenant=get_tenant(request))
        open_deals = all_deals.filter(
            stage__in=['new_click', 'contacted', 'interested', 'negotiating']
        )
        won_deals = all_deals.filter(stage='won')
        total_closed = all_deals.filter(stage__in=['won', 'lost']).count()

        # Avg velocity (hours new_click → won)
        avg_velocity = None
        won_timed = won_deals.exclude(new_click_at=None).exclude(won_at=None)
        if won_timed.exists():
            total_h = sum(
                (d.won_at - d.new_click_at).total_seconds() / 3600
                for d in won_timed
            )
            avg_velocity = round(total_h / won_timed.count(), 1)

        win_rate = None
        if total_closed > 0:
            win_rate = round(won_deals.count() / total_closed * 100, 1)

        return Response({
            'pipeline_value': open_deals.aggregate(
                v=Sum('estimated_value')
            )['v'] or Decimal('0'),
            'avg_deal_value': open_deals.aggregate(
                a=Sum('estimated_value')
            )['a'],
            'avg_velocity_hours': avg_velocity,
            'win_rate_percent': win_rate,
            'total_open_deals': open_deals.count(),
            'total_won_this_month': won_deals.filter(
                won_at__month=timezone.now().month
            ).count(),
            'deals_by_stage': {
                stage: all_deals.filter(stage=stage).count()
                for stage, _ in PipelineDeal.STAGE_CHOICES
            },
        })
