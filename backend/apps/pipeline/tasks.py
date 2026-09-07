from celery import shared_task
import logging
logger = logging.getLogger(__name__)

@shared_task
def flag_stale_deals():
    from django.utils import timezone
    from .models import PipelineDeal
    open_deals = PipelineDeal.objects.filter(stage__in=['new_click','contacted','interested','negotiating'])
    stale = 0
    for deal in open_deals:
        entry_time = getattr(deal, f"{deal.stage}_at", None) or deal.created_at
        if entry_time:
            days = (timezone.now() - entry_time).days
            if deal.days_in_current_stage != days:
                deal.days_in_current_stage = days
                deal.velocity = deal._compute_velocity()
                deal.save(update_fields=['days_in_current_stage','velocity'])
            if days >= 3:
                stale += 1
    if stale:
        from django.db.models import Count
        stale_by_tenant = (
            PipelineDeal.objects.filter(
                stage__in=['new_click','contacted','interested','negotiating'],
                days_in_current_stage__gte=3,
            ).values('tenant_id').annotate(count=Count('id'))
        )
        from apps.recommendations.tasks import create_r05_recommendation
        for row in stale_by_tenant:
            create_r05_recommendation.delay(str(row['tenant_id']), row['count'])
    logger.info(f"Pipeline velocity check: {stale} stale deals")
    return {'stale_deals': stale}
