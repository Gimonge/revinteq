"""
Revinteq v3 — Kommo Integration Models

Each Tenant connects their own Kommo account (own subdomain, own OAuth
tokens). Kommo is used purely as the sales pipeline/CRM — Revinteq does
not send messages through it. When a customer clicks a Meta ad, both
Kommo and Revinteq receive the same click event independently (Kommo via
its own Meta channel connection, Revinteq via the existing referral
webhooks). Revinteq then looks up the matching Kommo lead so that a
later "won" deal there can be attributed back to the ad/campaign that
produced it.
"""
from django.db import models
from apps.common.encryption import encrypt
from apps.tenants.models import Tenant
import uuid


class KommoConnection(models.Model):
    """One Kommo account connection per tenant."""

    id     = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE, related_name='kommo_connection'
    )

    subdomain = models.CharField(
        max_length=255,
        help_text="e.g. clientname.kommo.com — the tenant's own Kommo account"
    )

    # Each tenant registers their own integration inside their own Kommo
    # account, so these are per-tenant (not a shared Gimsc-wide app).
    client_id     = models.CharField(max_length=200, blank=True, default='')
    client_secret = encrypt(models.CharField(max_length=500, blank=True, default=''))

    access_token      = encrypt(models.TextField())
    refresh_token      = encrypt(models.TextField())
    token_expires_at  = models.DateTimeField(null=True, blank=True)

    sync_enabled = models.BooleanField(default=True)
    connected_at = models.DateTimeField(auto_now_add=True)
    last_synced  = models.DateTimeField(null=True, blank=True)
    last_error   = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'kommo_connections'

    def __str__(self):
        return f"{self.tenant.name} → {self.subdomain}"

    @property
    def is_token_expired(self):
        from django.utils import timezone
        return bool(self.token_expires_at and timezone.now() >= self.token_expires_at)

    @property
    def base_url(self):
        subdomain = self.subdomain
        if not subdomain.startswith('http'):
            subdomain = f"https://{subdomain}"
        return subdomain.rstrip('/')


class KommoMatchedLead(models.Model):
    """
    Links a Revinteq PipelineDeal (created from a Meta ad click) to the
    Kommo lead that Kommo independently created for the same click, so
    that a later "won" status on the Kommo side can be attributed back
    to the originating ad/campaign.
    """
    STATUS_CHOICES = [
        ('pending',   'Pending match'),     # created, still searching for the Kommo lead
        ('matched',   'Matched'),           # found the Kommo lead, tracking its status
        ('won',       'Won — synced as sale'),
        ('lost',      'Lost'),
        ('unmatched', 'Could not match'),   # gave up after retries
    ]
    MATCH_METHOD_CHOICES = [
        ('phone', 'Phone number (WhatsApp)'),
        ('time_window', 'Nearest in time (Messenger/Instagram)'),
    ]

    id     = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='kommo_matched_leads')

    pipeline_deal = models.OneToOneField(
        'pipeline.PipelineDeal', on_delete=models.CASCADE, related_name='kommo_match'
    )

    kommo_lead_id = models.CharField(max_length=100, blank=True, default='', db_index=True)
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    match_method  = models.CharField(max_length=20, choices=MATCH_METHOD_CHOICES, blank=True, default='')
    match_attempts = models.PositiveSmallIntegerField(default=0)

    won_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    won_at     = models.DateTimeField(null=True, blank=True)

    sale = models.OneToOneField(
        'sales.Sale', on_delete=models.SET_NULL, null=True, blank=True, related_name='kommo_matched_lead'
    )

    raw_lead_data = models.JSONField(default=dict, blank=True)

    matched_at   = models.DateTimeField(null=True, blank=True)
    last_checked = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'kommo_matched_leads'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['kommo_lead_id']),
        ]

    def __str__(self):
        return f"{self.tenant.name} | deal={self.pipeline_deal_id} | {self.status}"
