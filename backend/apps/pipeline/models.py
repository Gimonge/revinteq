"""
Revinteq v3 — Pipeline Models
Simplified journey: New Click → Won or Lost directly (optional middle stages).
WhatsApp conversations auto-create pipeline deals via Meta webhook.
"""
from django.db import models
from django.utils import timezone
from apps.tenants.models import Tenant
import uuid
import string
import random


class PipelineDeal(models.Model):

    STAGE_CHOICES = [
        ('new_click',   'New Click'),
        ('contacted',   'Contacted'),       # Optional
        ('interested',  'Interested'),      # Optional
        ('negotiating', 'Negotiating'),     # Optional
        ('won',         'Won'),
        ('lost',        'Lost'),
    ]

    VELOCITY_CHOICES = [
        ('hot',  'Hot'),
        ('warm', 'Warm'),
        ('cold', 'Cold'),
    ]

    SOURCE_CHOICES = [
        ('whatsapp_webhook',  'WhatsApp Webhook (Auto)'),
        ('messenger_webhook', 'Messenger Webhook (Auto)'),
        ('instagram_webhook', 'Instagram DM Webhook (Auto)'),
        ('meta_insights',     'Meta Insights Sync'),
        ('manual',            'Manual Entry'),
        ('mpesa',             'M-Pesa Auto-Match'),
    ]

    PLATFORM_CHOICES = [
        ('facebook',  'Facebook'),
        ('instagram', 'Instagram'),
        ('messenger', 'Messenger'),
        ('organic',   'Organic'),
        ('manual',    'Manual Entry'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name='pipeline_deals'
    )

    # Attribution
    ad = models.ForeignKey(
        'meta_integration.Ad', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='pipeline_deals'
    )
    campaign = models.ForeignKey(
        'meta_integration.Campaign', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='pipeline_deals'
    )
    # Conversation IDs per channel (for dedup)
    whatsapp_message_id = models.CharField(max_length=100, blank=True, db_index=True, default='')
    messenger_thread_id = models.CharField(max_length=100, blank=True, db_index=True, default='')
    instagram_thread_id = models.CharField(max_length=100, blank=True, db_index=True, default='')

    # ── M-Pesa Bill Reference ──────────────────────────────────────
    # Unique per deal. Customer types this in M-Pesa reference field.
    # Format: REV-XXX  e.g. REV-A3K  Auto-generated on save.
    mpesa_reference = models.CharField(max_length=20, unique=True, blank=True, db_index=True, default='')

    # Customer CRM link
    customer = models.ForeignKey(
        'customers.Customer', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='pipeline_deals'
    )

    platform = models.CharField(
        max_length=20, choices=PLATFORM_CHOICES, default='facebook'
    )
    source = models.CharField(
        max_length=30, choices=SOURCE_CHOICES, default='manual'
    )

    # Customer info (optional)
    customer_name = models.CharField(max_length=200, blank=True, default='')
    customer_phone = models.CharField(max_length=20, blank=True, default='')

    stage = models.CharField(
        max_length=20, choices=STAGE_CHOICES, default='new_click', db_index=True
    )
    estimated_value = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    velocity = models.CharField(
        max_length=10, choices=VELOCITY_CHOICES, default='cold'
    )
    notes = models.TextField(blank=True, default='')
    days_in_current_stage = models.PositiveIntegerField(default=0)

    # Stage timestamps
    new_click_at   = models.DateTimeField(null=True, blank=True)
    contacted_at   = models.DateTimeField(null=True, blank=True)
    interested_at  = models.DateTimeField(null=True, blank=True)
    negotiating_at = models.DateTimeField(null=True, blank=True)
    won_at         = models.DateTimeField(null=True, blank=True)
    lost_at        = models.DateTimeField(null=True, blank=True)

    # Loss reason (when marked lost)
    lost_reason = models.CharField(max_length=200, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    @staticmethod
    def _make_mpesa_reference():
        """Generate a unique REV-XXX reference (3 uppercase alphanumeric chars)."""
        chars = string.ascii_uppercase + string.digits
        while True:
            code = 'REV-' + ''.join(random.choices(chars, k=3))
            if not PipelineDeal.objects.filter(mpesa_reference=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.mpesa_reference:
            self.mpesa_reference = self._make_mpesa_reference()
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'pipeline_deals'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'stage']),
            models.Index(fields=['platform']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        name = self.customer_name or f"Deal #{str(self.id)[:6]}"
        return f"{name} | {self.get_stage_display()} | {self.platform}"

    STAGE_ORDER = [
        'new_click', 'contacted', 'interested',
        'negotiating', 'won', 'lost'
    ]

    def advance_to_stage(self, new_stage: str, notes: str = '', lost_reason: str = ''):
        """
        Move deal to any stage directly.
        Middle stages are optional — can jump from new_click straight to won or lost.
        """
        if new_stage not in dict(self.STAGE_CHOICES):
            raise ValueError(f"Invalid stage: {new_stage}")

        now = timezone.now()
        self.stage = new_stage

        stage_time_field = f"{new_stage}_at"
        if hasattr(self, stage_time_field) and not getattr(self, stage_time_field):
            setattr(self, stage_time_field, now)

        if new_stage == 'lost' and lost_reason:
            self.lost_reason = lost_reason

        if notes:
            self.notes = (self.notes + '\n' + notes).strip() if self.notes else notes

        self.days_in_current_stage = 0
        self.velocity = self._compute_velocity()
        self.save()

    def mark_won(self, notes: str = ''):
        """Shortcut: directly mark as Won."""
        self.advance_to_stage('won', notes=notes)

    def mark_lost(self, reason: str = '', notes: str = ''):
        """Shortcut: directly mark as Lost."""
        self.advance_to_stage('lost', notes=notes, lost_reason=reason)

    def _compute_velocity(self) -> str:
        if not self.created_at:
            return 'cold'
        elapsed_hours = (timezone.now() - self.created_at).total_seconds() / 3600
        if elapsed_hours < 24:
            return 'hot'
        elif elapsed_hours < 72:
            return 'warm'
        return 'cold'

    @property
    def total_velocity_hours(self):
        if not self.created_at:
            return None
        return round((timezone.now() - self.created_at).total_seconds() / 3600, 1)

    @property
    def is_stale(self):
        return self.days_in_current_stage >= 3

    @property
    def stage_color(self):
        return {
            'new_click':  '#2563EB',
            'contacted':  '#F97316',
            'interested': '#7C3AED',
            'negotiating':'#DB2777',
            'won':        '#16A34A',
            'lost':       '#EF4444',
        }.get(self.stage, '#94A3B8')


class StageTransitionLog(models.Model):
    """Immutable audit log of every stage change."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deal = models.ForeignKey(
        PipelineDeal, on_delete=models.CASCADE, related_name='transitions'
    )
    from_stage = models.CharField(max_length=20, blank=True, default='')
    to_stage = models.CharField(max_length=20)
    transitioned_at = models.DateTimeField(auto_now_add=True)
    transitioned_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True
    )
    notes = models.TextField(blank=True, default='')
    source = models.CharField(
        max_length=30, blank=True,
        help_text="manual | mpesa_auto | whatsapp_webhook", default='')

    class Meta:
        db_table = 'stage_transition_logs'
        ordering = ['transitioned_at']

    def __str__(self):
        return f"Deal {self.deal_id}: {self.from_stage} → {self.to_stage}"
