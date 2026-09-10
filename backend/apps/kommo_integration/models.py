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
    """
    One Kommo account connection per tenant, using a Long-lived Token —
    Kommo's recommended approach for private, single-account integrations
    like this one. No OAuth exchange, no refresh_token, no redirect URI.
    The client generates the token themselves (Settings -> Integrations
    -> their integration -> Keys and scopes -> Generate long-lived token)
    and pastes it in directly.
    """

    id     = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE, related_name='kommo_connection'
    )

    subdomain = models.CharField(
        max_length=255,
        help_text="e.g. clientname.kommo.com — the tenant's own Kommo account"
    )

    # The long-lived token itself (a JWT). No refresh_token exists for
    # this token type — when it expires, the tenant generates a new one.
    access_token = encrypt(models.TextField())
    token_expires_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Optional — set if the tenant tells us the expiry they chose (1 day to 5 years)"
    )

    sync_enabled = models.BooleanField(default=True)
    connected_at = models.DateTimeField(auto_now_add=True)
    last_synced  = models.DateTimeField(null=True, blank=True)
    last_error   = models.TextField(blank=True, default='')

    # Cache of this tenant's own Kommo pipeline structure — every client
    # names/orders their stages differently, so we fetch and store it
    # rather than assuming a fixed set. Refreshed periodically.
    # Shape: {"<status_id>": {"name": str, "sort": int, "pipeline_id": str, "pipeline_name": str}}
    pipeline_cache = models.JSONField(default=dict, blank=True)
    pipeline_cache_updated_at = models.DateTimeField(null=True, blank=True)

    # Total lead count per stage across the WHOLE Kommo account, independent
    # of ad-click matching (used for the funnel when Meta isn't connected
    # yet, or just to show the full picture regardless of attribution).
    # Shape: {"<stage_name>": count}
    funnel_counts_cache = models.JSONField(default=dict, blank=True)
    funnel_counts_updated_at = models.DateTimeField(null=True, blank=True)

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

    # The lead's actual current stage in the client's own Kommo pipeline
    # (e.g. "Qualified HOT", "Discovery Call Booked") — kept up to date by
    # the sync task independent of `status` above, which only tracks our
    # own pending/matched/won/lost/unmatched bookkeeping.
    kommo_status_id    = models.IntegerField(null=True, blank=True)
    kommo_status_name  = models.CharField(max_length=200, blank=True, default='')
    kommo_pipeline_id  = models.CharField(max_length=100, blank=True, default='')

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
