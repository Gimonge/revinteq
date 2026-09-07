"""Revinteq v3 — Recommendation Engine (live, no Celery required)"""
import logging
from datetime import date, timedelta
from django.utils import timezone
from apps.tenants.models import Tenant
from .models import Recommendation
from . import rules

logger = logging.getLogger(__name__)


class RecommendationEngine:
    def __init__(self, tenant: Tenant):
        self.tenant   = tenant
        self.currency = tenant.currency

    def run(self):
        """Evaluate all rules and persist new recommendations."""
        self._expire_stale()

        candidates = []

        # R01–R04: need MetricSnapshot — try live computation fallback
        snapshot, previous = self._get_snapshots()
        candidates += [
            rules.rule_r01(snapshot, previous, self.tenant),
            rules.rule_r02(snapshot, previous),
            rules.rule_r03(snapshot, self.tenant),
            rules.rule_r04(snapshot),
        ]

        # R05 — stale pipeline deals (live)
        try:
            from apps.pipeline.models import PipelineDeal
            stale = PipelineDeal.objects.filter(
                tenant=self.tenant,
                stage__in=['new_click', 'contacted', 'interested', 'negotiating'],
                days_in_current_stage__gte=3,
            ).count()
            candidates.append(rules.rule_r05(stale))
        except Exception as e:
            logger.error(f"R05 failed: {e}")

        # R06 — no recent sales (live)
        try:
            from apps.sales.models import Sale
            last = Sale.objects.filter(tenant=self.tenant).order_by('-sale_date').first()
            days = (date.today() - last.sale_date).days if last else 999
            candidates.append(rules.rule_r06(days))
        except Exception as e:
            logger.error(f'R06 failed: {e}')

        # R07 — Meta token expiry (live)
        try:
            from apps.meta_integration.models import AdAccount
            for acc in AdAccount.objects.filter(tenant=self.tenant):
                d = getattr(acc, 'days_until_token_expiry', None)
                if d is not None:
                    candidates.append(rules.rule_r07(d, acc.platform))
        except Exception as e:
            logger.error(f'R07 failed: {e}')

        # R09 — Meta not connected (always fires when FB/IG not connected)
        if not self.tenant.meta_fb_connected and not self.tenant.meta_ig_connected:
            candidates.append({
                'rule_id':  'R05',
                'title':    'Connect Facebook & Instagram Ads to unlock full analytics',
                'message':  f'Connect your Meta Ads account to track ad spend, ROI, and campaign performance for {self.tenant.name}. Go to Admin → Client Detail → Meta Setup.',
                'action':   'RECONNECT_META',
                'priority': 'INFO',
                'platform': 'facebook',
            })

        # R08 — sprint alert (live from RevenueGoal + Sales)
        try:
            goal_status, days_left, revenue_gap = self._get_goal_status()
            if goal_status == 'BEHIND' and days_left <= 7:
                candidates.append(rules.rule_r08(
                    'BEHIND', days_left, revenue_gap, self.currency
                ))
        except Exception as e:
            logger.error(f'R08 failed: {e}')

        expires_at = timezone.now() + timedelta(hours=48)
        saved = 0
        for rec_data in candidates:
            if not rec_data:
                continue
            try:
                # Delete any existing undismissed rec for same rule to avoid duplicates
                Recommendation.objects.filter(
                    tenant=self.tenant,
                    rule_id=rec_data['rule_id'],
                    is_dismissed=False,
                    is_applied=False,
                ).delete()
                # Some DBs have a legacy 'body' column — pass message as body too
                create_data = dict(rec_data)
                create_data['body'] = create_data.get('message', create_data.get('title', ''))
                try:
                    Recommendation.objects.create(
                        tenant=self.tenant,
                        expires_at=expires_at,
                        **create_data,
                    )
                except Exception:
                    # If 'body' field doesn't exist in model, try without it
                    Recommendation.objects.create(
                        tenant=self.tenant,
                        expires_at=expires_at,
                        **rec_data,
                    )
                saved += 1
                logger.info(f"Created {rec_data['rule_id']} for {self.tenant.name}")
            except Exception as e:
                logger.error(f"Failed to create {rec_data.get('rule_id','?')} for {self.tenant.name}: {e}")

        logger.info(f"Recommendations: {saved} new for {self.tenant.name}")
        return saved

    def run_r05(self, stale_count: int):
        rec = rules.rule_r05(stale_count)
        if rec:
            Recommendation.objects.get_or_create(
                tenant=self.tenant, rule_id='R05',
                is_dismissed=False, is_applied=False,
                defaults={**rec, 'expires_at': timezone.now() + timedelta(hours=48)},
            )

    def run_r07(self, days_left: int, platform: str):
        rec = rules.rule_r07(days_left, platform)
        if rec:
            Recommendation.objects.get_or_create(
                tenant=self.tenant, rule_id='R07',
                is_dismissed=False, is_applied=False,
                defaults={**rec, 'expires_at': timezone.now() + timedelta(hours=48)},
            )

    def _get_snapshots(self):
        """Try MetricSnapshot first, fall back to None (rules handle missing data)."""
        from apps.metrics.models import MetricSnapshot
        today = date.today()
        month_start = today.replace(day=1)
        prev_week = today - timedelta(days=today.weekday() + 7)
        try:
            current = MetricSnapshot.objects.get(
                tenant=self.tenant, period_type='month', period_start=month_start
            )
        except Exception:
            current = None
        try:
            previous = MetricSnapshot.objects.get(
                tenant=self.tenant, period_type='week', period_start=prev_week
            )
        except Exception:
            previous = None
        return current, previous

    def _get_goal_status(self):
        """Compute goal status live from Sales + RevenueGoal."""
        from apps.sales.models import Sale
        from apps.revenue_goals.models import RevenueGoal
        from django.db.models import Sum

        today = date.today()
        month_start = today.replace(day=1)

        goal_obj = RevenueGoal.objects.filter(
            tenant=self.tenant, month=month_start
        ).first()
        if not goal_obj:
            return 'no_goal', 0, 0

        target = float(goal_obj.target_amount)
        agg    = Sale.objects.filter(
            tenant=self.tenant, sale_date__gte=month_start, sale_date__lte=today
        ).aggregate(total=Sum('amount'))
        revenue = float(agg['total'] or 0)

        if today.month == 12:
            last_day = date(today.year, 12, 31)
        else:
            last_day = date(today.year, today.month + 1, 1) - timedelta(days=1)
        days_remaining = (last_day - today).days
        revenue_gap    = max(target - revenue, 0)

        if revenue >= target:
            goal_status = 'AHEAD'
        elif (revenue / target * 100) >= 60:
            goal_status = 'ON_TRACK'
        else:
            goal_status = 'BEHIND'

        return goal_status, days_remaining, revenue_gap

    def _expire_stale(self):
        try:
            Recommendation.objects.filter(
                tenant=self.tenant,
                is_applied=False,
                is_dismissed=False,
                expires_at__lt=timezone.now(),
            ).delete()
        except Exception as e:
            logger.warning(f"Could not expire stale recommendations: {e}")
