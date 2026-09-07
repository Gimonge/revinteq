from django.contrib import admin
from .models import RevenueGoal

@admin.register(RevenueGoal)
class RevenueGoalAdmin(admin.ModelAdmin):
    list_display  = ['tenant', 'month', 'target_amount', 'primary_channel']
    list_filter   = ['primary_channel']
    ordering      = ['-month']
