"""Revinteq v3 — WhatsApp Click Stats API"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

class WhatsAppClickStatsView(APIView):
    """GET /api/v1/whatsapp/stats/ — click counts for dashboard/analytics"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.common.views import get_tenant
        from apps.whatsapp_tracking.models import WhatsAppClick

        tenant = get_tenant(request)
        if not tenant:
            return Response({'total':0,'whatsapp':0,'messenger':0,'instagram':0,'by_campaign':[]})

        date_from = request.query_params.get('date_from')
        date_to   = request.query_params.get('date_to')

        qs = WhatsAppClick.objects.filter(tenant=tenant)

        if date_from:
            qs = qs.filter(clicked_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(clicked_at__date__lte=date_to)

        if not date_from and not date_to:
            now = timezone.now()
            qs  = qs.filter(clicked_at__year=now.year, clicked_at__month=now.month)

        from django.db.models import Count
        by_campaign = list(
            qs.filter(campaign__isnull=False)
            .values('campaign__name', 'platform')
            .annotate(clicks=Count('id'))
            .order_by('-clicks')[:10]
        )

        return Response({
            'total':       qs.count(),
            'whatsapp':    qs.filter(platform='whatsapp').count(),
            'messenger':   qs.filter(platform='messenger').count(),
            'instagram':   qs.filter(platform='instagram').count(),
            'by_campaign': [
                {'campaign': r['campaign__name'], 'platform': r['platform'], 'clicks': r['clicks']}
                for r in by_campaign
            ],
        })
