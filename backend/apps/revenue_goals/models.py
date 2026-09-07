"""Revinteq v3 — Revenue Goals"""
from django.db import models
from django.core.validators import MinValueValidator
from apps.tenants.models import Tenant
import uuid


class RevenueGoal(models.Model):
    CHANNEL_CHOICES = [
        ('whatsapp', 'WhatsApp DM'),
        ('website',  'Website orders'),
        ('walkin',   'Walk-in / Offline'),
    ]

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant         = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='revenue_goals')
    target_amount  = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(1)])
    month          = models.DateField(help_text="First day of the target month e.g. 2026-04-01")
    primary_channel= models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='whatsapp')
    notes = models.TextField(blank=True, default='')
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = 'revenue_goals'
        unique_together = ('tenant', 'month')
        ordering        = ['-month']

    def __str__(self):
        return f"{self.tenant.name} | {self.month.strftime('%B %Y')} | KES {self.target_amount:,.0f}"
