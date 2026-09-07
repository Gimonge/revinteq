"""
Revinteq v3 — External API Models
API keys for third-party integrations (POS, e-commerce, etc.)
Managed by admin, issued per tenant.
"""
from django.db import models
from apps.tenants.models import Tenant
import uuid
import secrets


def generate_api_key():
    """Generate a prefixed API key: rvq_live_XXXXXXXXXXXXXXXX"""
    return f"rvq_live_{secrets.token_urlsafe(32)}"


class ExternalAPIKey(models.Model):
    """
    API key for a third-party system to integrate with Revinteq.
    One tenant can have multiple keys (e.g. POS key + website key).
    All keys are managed by admin — clients cannot create their own.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name='api_keys'
    )
    name = models.CharField(
        max_length=100,
        help_text="Label for this key e.g. 'POS System', 'Website', 'Mobile App'"
    )
    key = models.CharField(
        max_length=100, unique=True, default=generate_api_key
    )
    is_active = models.BooleanField(default=True)
    # Permissions: what can this key do?
    can_create_sales = models.BooleanField(default=True)
    can_create_pipeline_deals = models.BooleanField(default=True)
    can_read_sales = models.BooleanField(default=True)
    can_read_metrics = models.BooleanField(default=False)

    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, related_name='created_api_keys'
    )
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'external_api_keys'
        verbose_name = 'External API Key'

    def __str__(self):
        return f"{self.tenant.name} — {self.name} ({'active' if self.is_active else 'revoked'})"


class WebhookEndpoint(models.Model):
    """
    A URL registered by the client's external system.
    Revinteq POSTs events to this URL when things happen.
    """
    EVENT_CHOICES = [
        ('sale.created',       'Sale Created'),
        ('sale.updated',       'Sale Updated'),
        ('pipeline.new_click', 'New Pipeline Click'),
        ('pipeline.won',       'Deal Marked Won'),
        ('pipeline.lost',      'Deal Marked Lost'),
        ('mpesa.received',     'M-Pesa Payment Received'),
        ('mpesa.matched',      'M-Pesa Payment Matched'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name='webhook_endpoints'
    )
    url = models.URLField(max_length=500)
    events = models.JSONField(
        default=list,
        help_text="List of event names to send to this URL"
    )
    secret = models.CharField(
        max_length=100, default=secrets.token_urlsafe,
        help_text="HMAC-SHA256 signing secret — include in webhook header verification"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'webhook_endpoints'

    def __str__(self):
        return f"{self.tenant.name} → {self.url}"


class WebhookDelivery(models.Model):
    """Log of every webhook delivery attempt."""
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('success',  'Success'),
        ('failed',   'Failed'),
        ('retrying', 'Retrying'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    endpoint = models.ForeignKey(
        WebhookEndpoint, on_delete=models.CASCADE, related_name='deliveries'
    )
    event = models.CharField(max_length=50)
    payload = models.JSONField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    response_status_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True, default='')
    attempt_count = models.PositiveIntegerField(default=0)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'webhook_deliveries'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event} → {self.endpoint.url} [{self.status}]"
