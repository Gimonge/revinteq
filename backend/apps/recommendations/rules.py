"""
Revinteq v3 — Recommendation Rules
Pure functions. Each returns a dict or None.
No DB writes — that happens in engine.py.
"""
from decimal import Decimal
from typing import Optional
from apps.metrics.engine import compute_max_budget_increase


def _rec(rule_id, title, message, action, priority, platform='', **kw) -> dict:
    return dict(rule_id=rule_id, title=title, message=message,
                action=action, priority=priority, platform=platform, **kw)


def rule_r01(snapshot, previous, tenant) -> Optional[dict]:
    """ROI >= 150% + revenue growing → increase budget."""
    if not snapshot or not snapshot.roi or snapshot.roi < Decimal('150'):
        return None
    if not previous or not previous.total_revenue or previous.total_revenue == 0:
        return None
    growth = (snapshot.total_revenue - previous.total_revenue) / previous.total_revenue * 100
    if growth < 5:
        return None
    cap    = tenant.budget_increase_cap_percent
    calc   = compute_max_budget_increase(Decimal('1200'), cap, 15)  # example budget
    ig_note= ' Instagram is outperforming Facebook — prioritise IG budget.' \
             if (snapshot.instagram_roi or 0) > (snapshot.facebook_roi or 0) else ''
    return _rec('R01',
        f'ROI is strong at {snapshot.roi:.1f}% — consider increasing budget',
        f'Your ROI is {snapshot.roi:.1f}% with revenue growing {growth:.1f}%. '
        f'Recommended increase: {tenant.currency} {calc["increase_amount"]:,.0f}/day '
        f'(capped at {cap}%). New budget: {tenant.currency} {calc["new_budget"]:,.0f}/day.{ig_note}',
        'INCREASE_BUDGET', 'HIGH',
        suggested_budget_increase_amount=float(calc['increase_amount']),
        suggested_new_budget=float(calc['new_budget']),
        budget_cap_applied_percent=float(cap),
    )


def rule_r02(snapshot, previous) -> Optional[dict]:
    """Spend up >20%, revenue flat → flag inefficiency."""
    if not snapshot or not previous or not previous.total_spend or previous.total_spend == 0:
        return None
    spend_growth = (snapshot.total_spend - previous.total_spend) / previous.total_spend * 100
    if spend_growth < 20:
        return None
    rev_growth = 0
    if previous.total_revenue and previous.total_revenue > 0:
        rev_growth = (snapshot.total_revenue - previous.total_revenue) / previous.total_revenue * 100
    if rev_growth >= 5:
        return None
    return _rec('R02',
        f'Spend up {spend_growth:.0f}% but revenue only grew {rev_growth:.0f}%',
        f'Your ad spend increased {spend_growth:.0f}% this period but revenue only grew {rev_growth:.0f}%. '
        f'Review your lowest-performing campaigns and consider pausing or revising ad creative.',
        'REVIEW_CAMPAIGN', 'MEDIUM',
    )


def rule_r03(snapshot, tenant) -> Optional[dict]:
    """Instagram AOV 15%+ higher than Facebook → reallocate budget."""
    if not snapshot or not snapshot.instagram_aov or not snapshot.facebook_aov:
        return None
    if snapshot.facebook_aov == 0:
        return None
    advantage = (snapshot.instagram_aov - snapshot.facebook_aov) / snapshot.facebook_aov * 100
    if advantage < 15:
        return None
    cap = tenant.budget_increase_cap_percent
    return _rec('R03',
        f'Instagram AOV is {advantage:.0f}% higher than Facebook',
        f'Instagram Average Order Value ({tenant.currency} {snapshot.instagram_aov:,.0f}) is '
        f'{advantage:.0f}% higher than Facebook ({tenant.currency} {snapshot.facebook_aov:,.0f}). '
        f'Consider reallocating 10–15% of Facebook budget to Instagram (within your {cap}% cap).',
        'REALLOCATE_BUDGET', 'HIGH', platform='instagram',
    )


def rule_r04(snapshot) -> Optional[dict]:
    """Conversion rate < 10% with enough data → review follow-up."""
    if not snapshot or not snapshot.conversion_rate:
        return None
    if snapshot.conversion_rate >= Decimal('10') or snapshot.total_conversations < 10:
        return None
    return _rec('R04',
        f'Conversion rate is low at {snapshot.conversion_rate:.1f}%',
        f'Only {snapshot.conversion_rate:.1f}% of WhatsApp conversations '
        f'({snapshot.total_sales} of {snapshot.total_conversations}) are converting to sales. '
        f'Review response speed and pricing.',
        'FOLLOW_UP', 'MEDIUM',
    )


def rule_r05(stale_count: int) -> Optional[dict]:
    """One or more pipeline deals stuck 3+ days."""
    if stale_count == 0:
        return None
    return _rec('R05',
        f'{stale_count} pipeline deal(s) stuck for 3+ days',
        f'You have {stale_count} deal(s) that have not moved in over 3 days. '
        f'Open your Sales Pipeline and follow up today.',
        'FOLLOW_UP', 'HIGH' if stale_count >= 3 else 'MEDIUM',
    )


def rule_r06(days_since_last_sale: int) -> Optional[dict]:
    """No sale logged in 3+ days."""
    if days_since_last_sale < 3:
        return None
    return _rec('R06',
        f'No sales logged in {days_since_last_sale} days',
        f'It has been {days_since_last_sale} days since your last sale was logged. '
        f'Log any offline or cash sales to keep your revenue GPS accurate.',
        'LOG_SALES', 'MEDIUM',
    )


def rule_r07(days_until_expiry: int, platform: str) -> Optional[dict]:
    """Meta token expiring within 7 days."""
    if days_until_expiry > 7:
        return None
    name = platform.title()
    return _rec('R07',
        f'{name} connection expires in {days_until_expiry} day(s)',
        f'Your {name} Ads connection will expire in {days_until_expiry} day(s). '
        f'Go to Settings → Connected Accounts and reconnect now — takes 30 seconds.',
        'RECONNECT_META', 'HIGH' if days_until_expiry <= 2 else 'MEDIUM', platform=platform,
    )


def rule_r08(goal_status: str, days_remaining: int, revenue_gap, currency: str = 'KES') -> Optional[dict]:
    """Behind goal with < 7 days remaining → sprint alert."""
    if goal_status != 'BEHIND' or days_remaining > 7:
        return None
    return _rec('R08',
        f'Sprint mode — {days_remaining} days left, {currency} {revenue_gap:,.0f} to go',
        f'You are behind your monthly goal with only {days_remaining} days remaining. '
        f'You need {currency} {revenue_gap:,.0f} more. Consider a flash sale, following up all '
        f'open pipeline deals, and temporarily increasing your best-performing ad budget.',
        'SPRINT_MODE', 'HIGH',
    )
