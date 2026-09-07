"""
Revinteq v3 — SMS Models
Africa's Talking integration.
Supports: manual SMS, automatic trigger-based SMS.
"""
from django.db import models
from apps.common.encryption import encrypt
from apps.tenants.models import Tenant
import uuid


class SMSConfig(models.Model):
    """Africa's Talking credentials per tenant. Managed by admin."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE, related_name='sms_config'
    )
    # Encrypted API key
    api_key = encrypt(models.CharField(max_length=200))
    username = models.CharField(max_length=100, help_text="Africa's Talking username")
    sender_id = models.CharField(
        max_length=20, blank=True,
        help_text="Registered sender ID e.g. AMARI. Leave blank to use default.", default='')
    is_active = models.BooleanField(default=True)
    # SMS credit balance (updated after each send)
    credit_balance = models.DecimalField(
        max_digits=10, decimal_places=4, default=0
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sms_configs'

    def __str__(self):
        return f"{self.tenant.name} — AT:{self.username}"


class SMSMessage(models.Model):
    """Log of every SMS sent through Revinteq."""
    STATUS_CHOICES = [
        ('queued',    'Queued'),
        ('sent',      'Sent'),
        ('delivered', 'Delivered'),
        ('failed',    'Failed'),
    ]

    SOURCE_CHOICES = [
        ('manual',    'Manual — sent by user'),
        ('auto',      'Automatic — triggered by rule'),
        ('bulk',      'Bulk — campaign send'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name='sms_messages'
    )
    recipient_number = models.CharField(max_length=20)
    recipient_name = models.CharField(max_length=200, blank=True, default='')
    message = models.TextField()
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    trigger = models.CharField(
        max_length=100, blank=True,
        help_text="Auto trigger name e.g. mpesa_payment_received", default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    # Africa's Talking message ID for delivery tracking
    at_message_id = models.CharField(max_length=100, blank=True, default='')
    at_status_code = models.CharField(max_length=20, blank=True, default='')
    cost = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sent_sms'
    )

    class Meta:
        db_table = 'sms_messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.recipient_number} | {self.status} | {self.created_at:%Y-%m-%d}"


class SMSTrigger(models.Model):
    """
    Automatic SMS rules per tenant.
    When a trigger event fires, send the configured message template.
    """
    TRIGGER_CHOICES = [
        ('mpesa_payment_received', 'M-Pesa Payment Received'),
        ('sale_confirmed',         'Sale Confirmed'),
        ('deal_went_cold',         'Pipeline Deal Went Cold (3+ days)'),
        ('goal_milestone_50',      'Revenue Goal 50% Reached'),
        ('goal_milestone_100',     'Revenue Goal 100% Reached'),
        ('deal_won',               'Deal Marked as Won'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name='sms_triggers'
    )
    trigger = models.CharField(max_length=100, choices=TRIGGER_CHOICES)
    message_template = models.TextField(
        help_text=(
            "Use placeholders: {amount}, {transaction_id}, "
            "{customer_name}, {product_name}, {business_name}"
        )
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sms_triggers'
        unique_together = ('tenant', 'trigger')

    def __str__(self):
        return f"{self.tenant.name} — {self.trigger} ({'ON' if self.is_active else 'OFF'})"

    def render_message(self, context: dict) -> str:
        """Fill in the template with actual values."""
        context.setdefault('business_name', self.tenant.name)
        try:
            return self.message_template.format(**context)
        except KeyError:
            return self.message_template
