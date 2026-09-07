from django.urls import path
from .views import RevenueGoalDetailView, RevenueGoalListCreateView, RevenueGoalStatusView

urlpatterns = [
    path('',        RevenueGoalListCreateView.as_view(), name='goals-list'),
    path('status/', RevenueGoalStatusView.as_view(),     name='goals-status'),
    path('<uuid:goal_id>/', RevenueGoalDetailView.as_view(), name='goal-detail'),
]
