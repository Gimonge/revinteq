"""Revinteq v3 — Recommendations Views"""
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.tenants.permissions import IsAdminOrSuperAdmin
from .models import Recommendation


class RecommendationSerializer(serializers.ModelSerializer):
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    action_display   = serializers.CharField(source='get_action_display',   read_only=True)
    tenant_name      = serializers.CharField(source='tenant.name', read_only=True)

    class Meta:
        model  = Recommendation
        fields = [
            'id', 'tenant_name', 'rule_id', 'title', 'message',
            'action', 'action_display', 'priority', 'priority_display', 'platform',
            'suggested_budget_increase_amount', 'suggested_new_budget',
            'budget_cap_applied_percent',
            'is_dismissed', 'is_applied',
            'generated_at', 'expires_at',
        ]


class AllRecommendationsView(APIView):
    """
    GET /api/v1/recommendations/
    Returns active recommendations across all tenants.
    Triggers the engine live on every request — no Celery needed.
    """
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def get(self, request):
        from apps.tenants.models import Tenant
        from .engine import RecommendationEngine
        import logging
        logger = logging.getLogger(__name__)

        tenant_id = request.query_params.get('tenant')

        # Run the engine live for all active tenants (or just the requested one)
        if tenant_id:
            tenants = Tenant.objects.filter(id=tenant_id, status__in=['active', 'trial'])
        else:
            tenants = Tenant.objects.filter(status__in=['active', 'trial'])

        for tenant in tenants:
            try:
                count = RecommendationEngine(tenant).run()
                logger.info(f"Engine ran for {tenant.name}: {count} new recommendations")
            except Exception as e:
                logger.error(f"Engine failed for {tenant.name}: {e}", exc_info=True)

        # Now return all active recommendations
        recs = Recommendation.objects.filter(
            is_dismissed=False,
            is_applied=False,
        ).exclude(
            expires_at__lt=timezone.now()
        ).select_related('tenant').order_by('-generated_at')

        if tenant_id:
            recs = recs.filter(tenant_id=tenant_id)

        # Also support ?is_dismissed=false filter from frontend
        is_dismissed = request.query_params.get('is_dismissed')
        if is_dismissed == 'false':
            recs = recs.filter(is_dismissed=False)

        return Response({
            'count':   recs.count(),
            'results': RecommendationSerializer(recs, many=True).data,
        })


class RecommendationDismissView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def post(self, request, rec_id):
        try:
            rec = Recommendation.objects.get(id=rec_id)
        except Recommendation.DoesNotExist:
            return Response({'error': True, 'message': 'Not found.'}, status=404)
        rec.is_dismissed = True
        rec.dismissed_at = timezone.now()
        rec.save(update_fields=['is_dismissed', 'dismissed_at'])
        return Response({'message': 'Dismissed.'})


class RecommendationApplyView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def post(self, request, rec_id):
        try:
            rec = Recommendation.objects.get(id=rec_id)
        except Recommendation.DoesNotExist:
            return Response({'error': True, 'message': 'Not found.'}, status=404)
        rec.is_applied = True
        rec.applied_at = timezone.now()
        rec.save(update_fields=['is_applied', 'applied_at'])
        return Response({'message': 'Applied.', 'recommendation': RecommendationSerializer(rec).data})
