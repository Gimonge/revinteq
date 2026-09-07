"""Revinteq v3 — Revenue Goals Views"""
from datetime import date
from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.tenants.permissions import IsClientOrAdmin
from apps.tenants.models import TenantUser
from .models import RevenueGoal


class RevenueGoalSerializer(serializers.ModelSerializer):
    month_display = serializers.SerializerMethodField()
    achieved      = serializers.SerializerMethodField()

    class Meta:
        model  = RevenueGoal
        fields = ['id', 'target_amount', 'month', 'month_display',
                  'achieved', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_month_display(self, obj):
        return obj.month.strftime('%B %Y') if obj.month else ''

    def get_achieved(self, obj):
        # Try to get revenue from metrics snapshot
        try:
            from apps.metrics.models import MetricSnapshot
            snap = MetricSnapshot.objects.filter(
                tenant=obj.tenant,
                period_type='month',
                period_start=obj.month,
            ).first()
            return float(snap.total_revenue) if snap else 0
        except Exception:
            return 0

    def validate_month(self, value):
        if value:
            return value.replace(day=1)
        return value

    def create(self, validated_data):
        tenant = self.context.get('tenant')
        if not tenant:
            raise serializers.ValidationError('No tenant found for this user.')
        validated_data['tenant'] = tenant
        # Check for duplicate month
        existing = RevenueGoal.objects.filter(
            tenant=tenant,
            month=validated_data['month']
        ).first()
        if existing:
            # Update existing instead of creating duplicate
            for k, v in validated_data.items():
                setattr(existing, k, v)
            existing.save()
            return existing
        return super().create(validated_data)


class RevenueGoalListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_tenant(self, request):
        """Get tenant from request, falling back to TenantUser lookup."""
        # Try request.tenant first (set by middleware)
        tenant = getattr(request, 'tenant', None)
        if tenant:
            return tenant
        # Fallback: look up directly from database
        tu = TenantUser.objects.select_related('tenant').filter(
            user=request.user
        ).first()
        return tu.tenant if tu else None

    def get(self, request):
        tenant = self._get_tenant(request)
        if not tenant:
            return Response({'error': True, 'message': 'No tenant found.'}, status=403)
        goals = RevenueGoal.objects.filter(tenant=tenant).order_by('-month')
        return Response(RevenueGoalSerializer(goals, many=True).data)

    def post(self, request):
        tenant = self._get_tenant(request)
        if not tenant:
            return Response({'error': True, 'message': 'No tenant found.'}, status=403)
        s = RevenueGoalSerializer(
            data=request.data,
            context={'request': request, 'tenant': tenant}
        )
        s.is_valid(raise_exception=True)
        goal = s.save()
        return Response(RevenueGoalSerializer(goal).data, status=status.HTTP_201_CREATED)


class RevenueGoalStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.metrics.models import MetricSnapshot

        tu = TenantUser.objects.select_related('tenant').filter(
            user=request.user
        ).first()
        tenant = getattr(request, 'tenant', None) or (tu.tenant if tu else None)

        if not tenant:
            return Response({'goal_status': 'NO_DATA'})

        month_str   = request.query_params.get('month')
        today       = date.today()
        month_start = date.fromisoformat(month_str).replace(day=1) if month_str else today.replace(day=1)

        try:
            snap = MetricSnapshot.objects.get(
                tenant=tenant, period_type='month', period_start=month_start
            )
            return Response({
                'month':                  month_start,
                'goal_status':            snap.goal_status,
                'revenue_goal':           snap.revenue_goal,
                'total_revenue':          snap.total_revenue,
                'revenue_gap':            snap.revenue_gap,
                'required_daily_revenue': snap.required_daily_revenue,
                'goal_progress_percent':  snap.goal_progress_percent,
                'avg_order_value':        snap.avg_order_value,
            })
        except MetricSnapshot.DoesNotExist:
            return Response({
                'month':       month_start,
                'goal_status': 'NO_DATA',
                'message':     'No metrics yet.',
            })


class RevenueGoalDetailView(APIView):
    """PATCH / DELETE /api/v1/revenue-goals/<goal_id>/"""
    permission_classes = [IsAuthenticated]

    def _get(self, request, goal_id):
        from apps.common.views import get_tenant
        from .models import RevenueGoal
        try:
            return RevenueGoal.objects.get(id=goal_id, tenant=get_tenant(request))
        except RevenueGoal.DoesNotExist:
            return None

    def patch(self, request, goal_id):
        from .serializers import RevenueGoalSerializer
        goal = self._get(request, goal_id)
        if not goal: return Response({'error': 'Not found.'}, status=404)
        s = RevenueGoalSerializer(goal, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)

    def delete(self, request, goal_id):
        goal = self._get(request, goal_id)
        if not goal: return Response({'error': 'Not found.'}, status=404)
        goal.delete()
        return Response(status=204)
