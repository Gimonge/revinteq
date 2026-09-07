from django.contrib import admin
from .models import PipelineDeal, StageTransitionLog

@admin.register(PipelineDeal)
class PipelineDealAdmin(admin.ModelAdmin):
    list_display  = ['tenant', 'customer_name', 'stage', 'platform', 'velocity', 'estimated_value', 'created_at']
    list_filter   = ['stage', 'platform', 'velocity']
    search_fields = ['customer_name', 'customer_phone']
    ordering      = ['-created_at']

@admin.register(StageTransitionLog)
class StageTransitionLogAdmin(admin.ModelAdmin):
    list_display = ['deal', 'from_stage', 'to_stage', 'transitioned_at', 'source']
    ordering     = ['-transitioned_at']
