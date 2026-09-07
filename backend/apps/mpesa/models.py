"""
Revinteq v3 — M-Pesa Models
Three flows:
  Flow 1: Automatic C2B (Daraja callback → auto-log sale + mark pipeline Won)
  Flow 2: STK Push (future)
  Flow 3: Manual entry (user selects M-Pesa, keys in amount + reference)
"""
from django.db import models
from apps.common.encryption import encrypt
from apps.tenants.models import Tenant
import uuid


class MPesaConfig(models.Model):
    """
    Daraja API credentials for one tenant.
    Supports both Till (Buy Goods) and Paybill.
    Managed by admin — clients cannot see or edit credentials.
    """
    SHORTCODE_TYPE_CHOICES = [
        ('till',    'Buy Goods (Till Number)'),
        ('paybill', 'Pay Bill'),
    ]

    ENVIRONMENT_CHOICES = [
        ('sandbox',    'Sandbox (Testing)'),
        ('production', 'Production (Live)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE, related_name='mpesa_config'
    )
    environment = models.CharField(
        max_length=20, choices=ENVIRONMENT_CHOICES, default='sandbox'
    )
    shortcode_type = models.CharField(
        max_length=20, choices=SHORTCODE_TYPE_CHOICES, default='till'
    )
    shortcode = models.CharField(
        max_length=20,
        help_text="Till number or Paybill number"
    )

    # Daraja API credentials — encrypted at rest
    consumer_key = encrypt(models.CharField(max_length=200))
    consumer_secret = encrypt(models.CharField(max_length=200))

    # For Paybill only
    account_reference = models.CharField(
        max_length=50, blank=True,
        help_text="Account number shown on Paybill prompt", default='')

    # Passkey for STK push (future)
    passkey = encrypt(models.CharField(max_length=200, blank=True))

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mpesa_configs'
        verbose_name = 'M-Pesa Configuration'

    def __str__(self):
        return f"{self.tenant.name} — {self.shortcode} ({self.shortcode_type})"

    @property
    def base_url(self):
        if self.environment == 'production':
            return 'https://api.safaricom.co.ke'
        return 'https://sandbox.safaricom.co.ke'


class MPesaTransaction(models.Model):
    """
    An incoming M-Pesa payment recorded by the Daraja C2B callback.
    Created automatically when Safaricom sends a callback to our endpoint.

    This is the raw record. It gets linked to a Sale and/or PipelineDeal
    by the matching engine (services/matcher.py).
    """
    STATUS_CHOICES = [
        ('received',  'Received'),     # Callback received, not yet matched
        ('matched',   'Matched'),      # Linked to a Sale + PipelineDeal
        ('unmatched', 'Unmatched'),    # Could not match — needs manual attention
        ('ignored',   'Ignored'),      # Test/invalid transaction
    ]

    TRANSACTION_TYPE_CHOICES = [
        ('c2b',       'C2B Payment'),
        ('stk_push',  'STK Push'),
        ('reversal',  'Reversal'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name='mpesa_transactions'
    )
    config = models.ForeignKey(
        MPesaConfig, on_delete=models.SET_NULL,
        null=True, related_name='transactions'
    )

    # Safaricom fields (from callback)
    transaction_id = models.CharField(
        max_length=50, unique=True,
        help_text="Safaricom transaction ID e.g. QK47XY8Z21"
    )
    transaction_type = models.CharField(
        max_length=20, choices=TRANSACTION_TYPE_CHOICES, default='c2b'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    msisdn = models.CharField(
        max_length=20, blank=True,
        help_text="Customer phone number (anonymised after matching, default='')"
    )
    first_name = models.CharField(max_length=100, blank=True, default='')
    middle_name = models.CharField(max_length=100, blank=True, default='')
    last_name = models.CharField(max_length=100, blank=True, default='')
    bill_ref_number = models.CharField(
        max_length=50, blank=True,
        help_text="Account reference / bill number entered by customer", default='')
    business_shortcode = models.CharField(max_length=20, blank=True, default='')
    transaction_time = models.DateTimeField(
        help_text="Time the payment was made, from Safaricom"
    )

    # Matching status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='received'
    )
    matched_sale = models.OneToOneField(
        'sales.Sale', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='mpesa_transaction'
    )
    matched_pipeline_deal = models.ForeignKey(
        'pipeline.PipelineDeal', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='mpesa_transactions'
    )

    # Raw callback data (stored for audit)
    raw_callback = models.JSONField(default=dict)

    received_at = models.DateTimeField(auto_now_add=True)
    matched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'mpesa_transactions'
        ordering = ['-transaction_time']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['transaction_time']),
        ]
        verbose_name = 'M-Pesa Transaction'
        verbose_name_plural = 'M-Pesa Transactions'

    def __str__(self):
        return f"{self.transaction_id} | KES {self.amount} | {self.status}"

    @property
    def payer_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        return ' '.join(p for p in parts if p).strip() or 'Unknown'
