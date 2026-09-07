"""
Revinteq v3 — Sales Model
Updated for multi-tenancy.
Supports all payment methods with appropriate reference fields.
M-Pesa: manual entry (Flow 3) and auto-logged (Flow 1).
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.tenants.models import Tenant
import uuid


class Sale(models.Model):

    PAYMENT_METHOD_CHOICES = [
        # M-Pesa
        ('mpesa_manual', 'M-Pesa (Manual entry)'),
        ('mpesa_auto',   'M-Pesa (Auto — Daraja callback)'),
        # Bank
        ('bank_deposit', 'Bank Deposit'),
        ('eft',          'EFT'),
        ('rtgs',         'RTGS'),
        ('standing_order', 'Standing Order'),
        # Other
        ('cash',         'Cash'),
        ('cheque',       'Cheque'),
        ('card',         'Card'),
        ('other',        'Other'),
    ]

    PLATFORM_SOURCE_CHOICES = [
        ('facebook',  'Facebook Ad'),
        ('instagram', 'Instagram Ad'),
        ('organic',   'Organic / Walk-in'),
        ('referral',  'Referral'),
        ('other',     'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Multi-tenancy
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name='sales'
    )

    # Attribution chain (all optional)
    pipeline_deal = models.OneToOneField(
        'pipeline.PipelineDeal', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sale'
    )
    ad = models.ForeignKey(
        'meta_integration.Ad', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sales'
    )
    campaign = models.ForeignKey(
        'meta_integration.Campaign', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sales'
    )

    # Customer info (optional — linked or anonymous)
    customer_name  = models.CharField(max_length=200, blank=True, default='')
    customer_phone = models.CharField(max_length=20,  blank=True, default='')

    # Sale details
    product_name = models.CharField(max_length=300)
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('1'))]
    )
    payment_method = models.CharField(
        max_length=30, choices=PAYMENT_METHOD_CHOICES, default='cash'
    )

    # Payment reference — label changes based on payment method
    # M-Pesa:        Transaction code e.g. QK47XY8Z21
    # Cheque:        Cheque number
    # Bank/EFT/RTGS: Bank reference number
    # Card:          Card receipt number
    # Cash:          Left blank
    payment_reference = models.CharField(
        max_length=100, blank=True,
        help_text=(
            "M-Pesa: transaction code | "
            "Bank: reference number | "
            "Cheque: cheque number | "
            "Card: receipt number"
        ), default=''
    )

    # Alias for M-Pesa specifically (same field, kept for clarity in code)
    @property
    def mpesa_reference(self):
        return self.payment_reference

    platform_source = models.CharField(
        max_length=20, choices=PLATFORM_SOURCE_CHOICES, default='facebook'
    )
    sale_date = models.DateField()
    is_confirmed = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default='')

    # Bulk upload tracking
    bulk_upload = models.ForeignKey(
        'bulk_upload.BulkSalesUpload', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sales'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='logged_sales'
    )

    class Meta:
        db_table = 'sales'
        ordering = ['-sale_date', '-created_at']
        indexes = [
            models.Index(fields=['tenant', 'sale_date']),
            models.Index(fields=['platform_source']),
            models.Index(fields=['payment_method']),
        ]

    def __str__(self):
        return (
            f"{self.product_name} | {self.tenant.currency} {self.amount} | "
            f"{self.sale_date} | {self.payment_method}"
        )

    @property
    def payment_reference_label(self):
        """Human-readable label for the reference field based on payment method."""
        labels = {
            'mpesa_manual': 'M-Pesa Transaction Code',
            'mpesa_auto':   'M-Pesa Transaction Code',
            'bank_deposit': 'Bank Reference Number',
            'eft':          'EFT Reference Number',
            'rtgs':         'RTGS Reference Number',
            'standing_order': 'Standing Order Reference',
            'cheque':       'Cheque Number',
            'card':         'Card Receipt Number',
            'cash':         None,  # No reference for cash
            'other':        'Reference Number',
        }
        return labels.get(self.payment_method, 'Reference')

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)

        # Auto-advance pipeline deal to Won when sale is logged
        if is_new and self.pipeline_deal and self.pipeline_deal.stage != 'won':
            self.pipeline_deal.advance_to_stage('won')
