from django.contrib import admin
from .models import Recommendation

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display  = ['tenant', 'rule_id', 'priority', 'title', 'is_dismissed', 'is_applied', 'generated_at']
    list_filter   = ['priority', 'rule_id', 'is_dismissed', 'is_applied']
    readonly_fields = ['generated_at']
    ordering      = ['-generated_at']
