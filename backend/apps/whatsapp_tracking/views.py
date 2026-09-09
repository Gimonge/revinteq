"""
Revinteq v3 — WhatsApp Click Stats API

NOTE: this previously queried the WhatsAppClick model, which nothing in
the codebase ever actually creates — every real ad-click webhook
(WhatsApp/Messenger/Instagram) creates a PipelineDeal instead, so this
endpoint was silently returning all-zero counts. Rewritten to query
PipelineDeal, which is what's actually populated. Channel (WhatsApp vs
Messenger vs Instagram DM) is tracked on `source`, not `platform` —
`platform` is the ad placement (Facebook/Instagram), a different thing.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count

CHANNEL_SOURCES = {
    'whatsapp':  'whatsapp_webhook',
    'messenger': 'messenger_webhook',
    'instagram': 'instagram_webhook',
}


class WhatsAppClickStatsView(APIView):
    """GET /api/v1/whatsapp/stats/ — click/conversation counts for dashboard/analytics"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.common.views import get_tenant
        from apps.pipeline.models import PipelineDeal

        tenant = get_tenant(request)
        if not tenant:
            return Response({'total': 0, 'whatsapp': 0, 'messenger': 0, 'instagram': 0,
                              'synced_to_sale': 0, 'by_campaign': []})

        date_from = request.query_params.get('date_from')
        date_to   = request.query_params.get('date_to')

        qs = PipelineDeal.objects.filter(
            tenant=tenant, source__in=CHANNEL_SOURCES.values()
        )

        if date_from:
            qs = qs.filter(new_click_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(new_click_at__date__lte=date_to)
        if not date_from and not date_to:
            now = timezone.now()
            qs = qs.filter(new_click_at__year=now.year, new_click_at__month=now.month)

        by_campaign = list(
            qs.filter(campaign__isnull=False)
            .values('campaign__name', 'platform')
            .annotate(clicks=Count('id'))
            .order_by('-clicks')[:10]
        )

        # Only "synced to a Won sale via Kommo" matters here — no other
        # Kommo stage is tracked for dashboard purposes.
        synced_to_sale = qs.filter(sale__isnull=False).count()

        return Response({
            'total':          qs.count(),
            'whatsapp':       qs.filter(source=CHANNEL_SOURCES['whatsapp']).count(),
            'messenger':      qs.filter(source=CHANNEL_SOURCES['messenger']).count(),
            'instagram':      qs.filter(source=CHANNEL_SOURCES['instagram']).count(),
            'synced_to_sale': synced_to_sale,
            'by_campaign': [
                {'campaign': r['campaign__name'], 'platform': r['platform'], 'clicks': r['clicks']}
                for r in by_campaign
            ],
        })
