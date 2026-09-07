"""
Revinteq v3 — Meta Integration Models
Facebook + Instagram ad accounts, campaigns, ads, daily spend records.
All OAuth tokens encrypted at rest. All data scoped to a Tenant.
"""
from django.db import models
from apps.common.encryption import encrypt
from apps.tenants.models import Tenant
import uuid


class AdAccount(models.Model):
    PLATFORM_CHOICES = [
        ('facebook',  'Facebook'),
        ('instagram', 'Instagram'),
        ('both',      'Facebook & Instagram'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name='ad_accounts'
    )
    meta_account_id = models.CharField(max_length=100, unique=True)
    account_name    = models.CharField(max_length=200, blank=True, default='')
    assigned_tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_ad_accounts',
        help_text='Tenant this ad account is attributed to for sales reporting'
    )
    platform        = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='both')

    access_token     = encrypt(models.TextField())
    token_expires_at = models.DateTimeField(null=True, blank=True)

    instagram_business_account_id = models.CharField(max_length=100, blank=True, default='')
    instagram_username = models.CharField(max_length=100, blank=True, default='')

    last_synced  = models.DateTimeField(null=True, blank=True)
    sync_enabled = models.BooleanField(default=True)
    currency     = models.CharField(max_length=3, default='KES')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ad_accounts'

    def __str__(self):
        return f"{self.account_name or self.meta_account_id} ({self.platform})"

    @property
    def is_token_expired(self):
        from django.utils import timezone
        return bool(self.token_expires_at and timezone.now() >= self.token_expires_at)

    @property
    def days_until_token_expiry(self):
        from django.utils import timezone
        if not self.token_expires_at:
            return None
        return (self.token_expires_at - timezone.now()).days


class Campaign(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'), ('PAUSED', 'Paused'),
        ('DELETED', 'Deleted'), ('ARCHIVED', 'Archived'),
    ]
    OBJECTIVE_CHOICES = [
        ('CONVERSIONS', 'Conversions'), ('MESSAGES', 'Messages'),
        ('TRAFFIC', 'Traffic'), ('REACH', 'Reach'),
        ('BRAND_AWARENESS', 'Brand Awareness'), ('VIDEO_VIEWS', 'Video Views'),
        ('LEAD_GENERATION', 'Lead Generation'), ('OTHER', 'Other'),
    ]
    PLATFORM_CHOICES = [
        ('facebook', 'Facebook'), ('instagram', 'Instagram'), ('both', 'Both'),
    ]

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ad_account       = models.ForeignKey(AdAccount, on_delete=models.CASCADE, related_name='campaigns')
    meta_campaign_id = models.CharField(max_length=100, unique=True)
    name             = models.CharField(max_length=300)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    objective        = models.CharField(max_length=50, choices=OBJECTIVE_CHOICES, default='OTHER')
    platform         = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='both')
    daily_budget     = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campaigns'

    def __str__(self):
        return f"{self.name} ({self.platform})"

    @property
    def tenant(self):
        return self.ad_account.tenant

    @property
    def budget_cap_percent(self):
        return self.ad_account.tenant.budget_increase_cap_percent

    @property
    def max_recommended_budget(self):
        if not self.daily_budget:
            return None
        from decimal import Decimal
        return self.daily_budget * (1 + Decimal(str(self.budget_cap_percent)) / 100)

    @property
    def max_allowed_increase(self):
        if not self.daily_budget:
            return None
        from decimal import Decimal
        return self.daily_budget * (Decimal(str(self.budget_cap_percent)) / 100)


class Ad(models.Model):
    FORMAT_CHOICES = [
        ('IMAGE', 'Image'), ('VIDEO', 'Video'), ('CAROUSEL', 'Carousel'),
        ('REEL', 'Reel'), ('STORY', 'Story'), ('COLLECTION', 'Collection'),
        ('OTHER', 'Other'),
    ]
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'), ('PAUSED', 'Paused'), ('DELETED', 'Deleted'),
        ('ARCHIVED', 'Archived'), ('IN_REVIEW', 'In Review'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign    = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='ads')
    meta_ad_id  = models.CharField(max_length=100, unique=True)
    name        = models.CharField(max_length=300)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    ad_format   = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='IMAGE')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ads'

    def __str__(self):
        return f"{self.name} ({self.ad_format})"

    @property
    def tenant(self):
        return self.campaign.ad_account.tenant


class AdSpendRecord(models.Model):
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ad             = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='spend_records')
    date           = models.DateField()
    spend          = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    impressions    = models.PositiveIntegerField(default=0)
    clicks         = models.PositiveIntegerField(default=0)
    dm_conversations = models.PositiveIntegerField(default=0)
    is_partial     = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ad_spend_records'
        unique_together = ('ad', 'date')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['ad', 'date']),
        ]

    def __str__(self):
        return f"{self.ad.name} | {self.date} | KES {self.spend}"
