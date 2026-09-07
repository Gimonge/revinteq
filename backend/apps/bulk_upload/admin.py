from django.contrib import admin
from .models import BulkSalesUpload

@admin.register(BulkSalesUpload)
class BulkSalesUploadAdmin(admin.ModelAdmin):
    list_display  = ['tenant', 'original_filename', 'status', 'total_rows', 'valid_rows', 'saved_rows', 'created_at']
    list_filter   = ['status']
    readonly_fields = ['created_at', 'completed_at']
