"""
Revinteq v3 — Tenants Models
Core multi-tenancy. Every piece of data in the system
belongs to a Tenant. Tenants are completely isolated from each other.

Roles:
  SUPER_ADMIN — Gimsc Solutions staff. Full access to all tenants.
  ADMIN       — Gimsc staff with limited scope. Cannot manage billing.
  CLIENT      — The business owner. Sees only their own tenant data.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
import uuid


class Tenant(models.Model):
    """
    One Tenant = one client business managed by Gimsc Solutions.
    e.g. Amari Boutique Nairobi, Zuri Cosmetics Mombasa.
    All data in the system (Sales, Pipeline, Metrics etc.) is scoped to a Tenant.
    """
    STATUS_CHOICES = [
        ('active',   'Active'),
        ('inactive', 'Inactive'),
    ]

    CURRENCY_CHOICES = [
        ('KES', 'Kenyan Shilling'),
        ('UGX', 'Ugandan Shilling'),
        ('TZS', 'Tanzanian Shilling'),
        ('USD', 'US Dollar'),
        ('GBP', 'British Pound'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Business trading name")
    slug = models.SlugField(max_length=100, unique=True, help_text="URL-safe identifier e.g. amari-boutique")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='KES')

    # Contact
    contact_name = models.CharField(max_length=200, blank=True, default='')
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True, default='')

    # Business details
    whatsapp_number = models.CharField(max_length=20, blank=True, default='')
    whatsapp_default_message = models.TextField(blank=True, default='')
    industry = models.CharField(max_length=100, blank=True, default='')
    location = models.CharField(max_length=200, blank=True, default='')

    # Budget cap per tenant (5–30%, default 20%)
    budget_increase_cap_percent = models.PositiveIntegerField(
        default=20,
        validators=[MinValueValidator(5)],
    )

    # Meta (Facebook + Instagram) connection flags
    meta_fb_connected = models.BooleanField(default=False)
    meta_fb_access_token    = models.TextField(blank=True, default='')
    meta_fb_token_expires_at= models.DateTimeField(null=True, blank=True)
    meta_ig_connected = models.BooleanField(default=False)

    # Onboarding
    onboarding_complete = models.BooleanField(default=False)
    onboarded_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Internal notes by Gimsc admin", default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_tenants'
    )

    class Meta:
        db_table = 'tenants'
        ordering = ['name']
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'

    def __str__(self):
        return f"{self.name} [{self.status}]"

    @property
    def max_budget_increase_factor(self):
        return 1 + (self.budget_increase_cap_percent / 100)


class TenantUser(models.Model):
    """
    Links a Django User to a Tenant with a specific role.
    One user can belong to multiple tenants (e.g. Gimsc admin).
    One tenant can have multiple users (future: staff accounts).
    """
    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Admin'),   # Gimsc Solutions — full access
        ('ADMIN',       'Admin'),          # Gimsc staff — limited
        ('CLIENT',      'Client'),         # Business owner — own data only
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='tenant_memberships'
    )
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name='memberships'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CLIENT')
    is_active = models.BooleanField(default=True)

    # Admin impersonation: when a SUPER_ADMIN is acting as this client
    # we track it in the session, not here
    joined_at = models.DateTimeField(auto_now_add=True)
    invited_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sent_invitations'
    )

    class Meta:
        db_table = 'tenant_users'
        unique_together = ('user', 'tenant')
        verbose_name = 'Tenant User'
        verbose_name_plural = 'Tenant Users'

    def __str__(self):
        return f"{self.user.email} → {self.tenant.name} [{self.role}]"

    @property
    def is_super_admin(self):
        return self.role == 'SUPER_ADMIN'

    @property
    def is_admin(self):
        return self.role in ('SUPER_ADMIN', 'ADMIN')

    @property
    def is_client(self):
        return self.role == 'CLIENT'


class TenantInvitation(models.Model):
    """
    Invitation sent to a new client to join their portal.
    Admin generates the invitation link; client clicks it to set password.
    """
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('accepted', 'Accepted'),
        ('expired',  'Expired'),
        ('revoked',  'Revoked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name='invitations'
    )
    email = models.EmailField()
    role = models.CharField(max_length=20, default='CLIENT')
    token = models.CharField(max_length=128, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    invited_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='invitations_sent'
    )
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tenant_invitations'

    def __str__(self):
        return f"Invite: {self.email} → {self.tenant.name} [{self.status}]"
