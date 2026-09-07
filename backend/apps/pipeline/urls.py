from django.urls import path
from .views import (
    PipelineBoardView, PipelineDealListCreateView,
    PipelineDealDetailView,
    PipelineDealActionView, PipelineDealAdvanceView, PipelineSummaryView,
)

urlpatterns = [
    path('board/',                              PipelineBoardView.as_view(),          name='pipeline-board'),
    path('summary/',                            PipelineSummaryView.as_view(),        name='pipeline-summary'),
    path('deals/',                              PipelineDealListCreateView.as_view(), name='pipeline-deals'),
    path('deals/<uuid:deal_id>/',               PipelineDealDetailView.as_view(),     name='pipeline-deal-detail'),
    path('deals/<str:deal_id>/',                PipelineDealDetailView.as_view(),     name='pipeline-deal-detail-str'),
    path('deals/<uuid:deal_id>/action/',        PipelineDealActionView.as_view(),     name='pipeline-action'),
    path('deals/<str:deal_id>/action/',         PipelineDealActionView.as_view(),     name='pipeline-action-str'),
    path('deals/<uuid:deal_id>/advance/',       PipelineDealAdvanceView.as_view(),    name='pipeline-advance'),
    path('deals/<str:deal_id>/advance/',        PipelineDealAdvanceView.as_view(),    name='pipeline-advance-str'),
]
