from django.urls import path
from .views import AllRecommendationsView, RecommendationDismissView, RecommendationApplyView
urlpatterns = [
    path('',                       AllRecommendationsView.as_view(),   name='rec-list'),
    path('<uuid:rec_id>/dismiss/', RecommendationDismissView.as_view(),name='rec-dismiss'),
    path('<uuid:rec_id>/apply/',   RecommendationApplyView.as_view(),  name='rec-apply'),
]
