"""
Revinteq v3 — Metrics Engine
Pure functions. No DB calls. Fully testable.
Division-by-zero always returns None, never 0.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional


def safe_div(num, den) -> Optional[Decimal]:
    if not den or Decimal(str(den)) == 0:
        return None
    return Decimal(str(num)) / Decimal(str(den))


def q2(val) -> Decimal:
    return val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if val else val


def compute_roi(revenue, spend) -> Optional[Decimal]:
    r = safe_div(Decimal(str(revenue)) - Decimal(str(spend)), spend)
    return q2(r * 100) if r is not None else None


def compute_cost_per_conversion(spend, conversations) -> Optional[Decimal]:
    return q2(safe_div(spend, conversations))


def compute_cost_per_sale(spend, sales) -> Optional[Decimal]:
    return q2(safe_div(spend, sales))


def compute_conversion_rate(sales, conversations) -> Optional[Decimal]:
    r = safe_div(sales, conversations)
    return r.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP) * 100 if r else None


def compute_aov(revenue, sales) -> Optional[Decimal]:
    return q2(safe_div(revenue, sales))


def compute_revenue_per_client(revenue, unique_clients) -> Optional[Decimal]:
    return q2(safe_div(revenue, unique_clients))


def compute_revenue_gap(goal, actual) -> Optional[Decimal]:
    if goal is None:
        return None
    return Decimal(str(goal)) - Decimal(str(actual))


def compute_required_daily_revenue(gap, days_remaining) -> Optional[Decimal]:
    if gap is None:
        return None
    g = Decimal(str(gap))
    if g <= 0:
        return Decimal('0.00')
    return q2(safe_div(g, days_remaining))


def compute_goal_progress(revenue, goal) -> Optional[Decimal]:
    r = safe_div(revenue, goal)
    return q2(r * 100) if r else None


def determine_goal_status(actual, goal, days_remaining, total_days) -> str:
    if not goal or goal == 0:
        return 'NO_GOAL'
    elapsed = total_days - days_remaining
    if total_days <= 0 or elapsed <= 0:
        return 'ON_TRACK'
    fraction = Decimal(str(elapsed)) / Decimal(str(total_days))
    expected = Decimal(str(goal)) * fraction
    act      = Decimal(str(actual))
    if act >= expected * Decimal('1.05'):
        return 'AHEAD'
    if act < expected * Decimal('0.90'):
        return 'BEHIND'
    return 'ON_TRACK'


def compute_max_budget_increase(current_budget, cap_percent: int, desired_percent: int) -> dict:
    budget  = Decimal(str(current_budget))
    max_inc = budget * (Decimal(str(cap_percent)) / 100)
    desired = budget * (Decimal(str(desired_percent)) / 100)
    capped  = desired > max_inc
    actual  = min(desired, max_inc)
    return {
        'current_budget': budget,
        'increase_amount': q2(actual),
        'new_budget':      q2(budget + actual),
        'cap_applied':     capped,
        'cap_percent':     cap_percent,
    }

def compute_roas(revenue, spend) -> Optional[Decimal]:
    """Return on Ad Spend = Revenue / Spend. A ROAS of 3x means KES 3 earned per KES 1 spent."""
    return q2(safe_div(revenue, spend))

def compute_cpl(spend, leads) -> Optional[Decimal]:
    """Cost Per Lead = Spend / Number of Pipeline Deals created."""
    return q2(safe_div(spend, leads))

def compute_cpa(spend, sales) -> Optional[Decimal]:
    """Cost Per Acquisition = Spend / Number of Confirmed Sales."""
    return q2(safe_div(spend, sales))
