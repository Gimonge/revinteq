from django.urls import path
from .views import (
    SaleListCreateView, SaleDetailView, SalesSummaryView,
    PaymentMethodChoicesView, DailySalesView,
)

urlpatterns = [
    path('',                 SaleListCreateView.as_view(),       name='sale-list'),
    path('<uuid:sale_id>/',  SaleDetailView.as_view(),           name='sale-detail'),
    path('summary/',         SalesSummaryView.as_view(),         name='sale-summary'),
    path('payment-methods/', PaymentMethodChoicesView.as_view(), name='payment-methods'),
    path('daily/',           DailySalesView.as_view(),           name='sale-daily'),
]
