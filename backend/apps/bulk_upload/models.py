"""
Revinteq v3 — Bulk Sales Upload Models
Excel upload → preview → confirm → batch save.
"""
from django.db import models
from apps.tenants.models import Tenant
import uuid


class BulkSalesUpload(models.Model):
    """
    Tracks one bulk upload session.
    Flow: uploaded → previewed → confirmed → processed
    """
    STATUS_CHOICES = [
        ('uploaded',   'Uploaded — awaiting preview'),
        ('previewed',  'Previewed — awaiting confirmation'),
        ('processing', 'Processing'),
        ('completed',  'Completed'),
        ('failed',     'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name='bulk_uploads'
    )
    file = models.FileField(upload_to='bulk_uploads/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='uploaded'
    )
    total_rows = models.PositiveIntegerField(default=0)
    valid_rows = models.PositiveIntegerField(default=0)
    error_rows = models.PositiveIntegerField(default=0)
    saved_rows = models.PositiveIntegerField(default=0)
    preview_data = models.JSONField(default=list, help_text="Parsed rows for preview")
    error_summary = models.JSONField(default=list, help_text="List of row errors")
    uploaded_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, related_name='bulk_uploads'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'bulk_sales_uploads'
        ordering = ['-created_at']

    def __str__(self):
        return (
            f"{self.tenant.name} | {self.original_filename} | "
            f"{self.saved_rows}/{self.total_rows} | {self.status}"
        )
