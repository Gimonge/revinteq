# Revinteq v3 — WhatsApp Tracking Models
from django.db import models
import uuid

class WhatsAppClick(models.Model):
    """Records each WhatsApp click from a Meta ad — no pipeline deal created."""
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant         = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='whatsapp_clicks')
    ad             = models.ForeignKey('meta_integration.Ad', on_delete=models.SET_NULL, null=True, blank=True)
    campaign       = models.ForeignKey('meta_integration.Campaign', on_delete=models.SET_NULL, null=True, blank=True)
    platform       = models.CharField(max_length=20, default='whatsapp')  # whatsapp, messenger, instagram
    message_id     = models.CharField(max_length=100, blank=True, db_index=True)
    sender_phone   = models.CharField(max_length=30, blank=True)
    clicked_at     = models.DateTimeField(auto_now_add=True)
    meta_ad_id     = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'whatsapp_clicks'
        ordering = ['-clicked_at']
        indexes = [
            models.Index(fields=['tenant', 'clicked_at']),
            models.Index(fields=['campaign', 'clicked_at']),
        ]

    def __str__(self):
        return f"{self.tenant} | {self.platform} | {self.clicked_at.date()}"
