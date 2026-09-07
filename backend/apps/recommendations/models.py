"""Revinteq v3 — Recommendations Model"""
from django.db import models
from apps.tenants.models import Tenant
import uuid


class Recommendation(models.Model):
    PRIORITY_CHOICES = [('HIGH','High'),('MEDIUM','Medium'),('LOW','Low'),('INFO','Info')]
    ACTION_CHOICES   = [
        ('INCREASE_BUDGET',   'Increase Budget'),
        ('REDUCE_BUDGET',     'Reduce Budget'),
        ('REVIEW_CAMPAIGN',   'Review Campaign'),
        ('REALLOCATE_BUDGET', 'Reallocate Budget'),
        ('FOLLOW_UP',         'Follow Up'),
        ('LOG_SALES',         'Log Sales'),
        ('RECONNECT_META',    'Reconnect Meta'),
        ('SPRINT_MODE',       'Sprint Mode'),
        ('INFORMATIONAL',     'Informational'),
    ]
    RULE_CHOICES = [
        ('R01','R01 — ROI + Growth → Increase Budget'),
        ('R02','R02 — Spend Up, Revenue Flat'),
        ('R03','R03 — Instagram AOV Shift'),
        ('R04','R04 — Low Conversion Rate'),
        ('R05','R05 — Pipeline Deal Stale'),
        ('R06','R06 — No Sales Logged'),
        ('R07','R07 — Meta Token Expiry'),
        ('R08','R08 — Behind Goal Sprint Alert'),
    ]

    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant   = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='recommendations')
    rule_id  = models.CharField(max_length=10, choices=RULE_CHOICES)
    title    = models.CharField(max_length=300)
    message  = models.TextField()
    body     = models.TextField(default='')  # legacy alias for message
    action   = models.CharField(max_length=30, choices=ACTION_CHOICES, default='INFORMATIONAL')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='INFO')
    platform = models.CharField(max_length=20, blank=True, default='')

    suggested_budget_increase_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    suggested_new_budget             = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    budget_cap_applied_percent       = models.DecimalField(max_digits=5,  decimal_places=2, null=True, blank=True)

    is_dismissed = models.BooleanField(default=False)
    is_applied   = models.BooleanField(default=False)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    applied_at   = models.DateTimeField(null=True, blank=True)

    generated_at = models.DateTimeField(auto_now_add=True)
    expires_at   = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'recommendations'
        ordering = ['-generated_at']
        indexes  = [models.Index(fields=['tenant', 'is_dismissed'])]

    def __str__(self):
        return f"[{self.priority}] {self.rule_id}: {self.title}"
