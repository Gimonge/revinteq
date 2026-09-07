from django.urls import path
from .views import CustomerListView, CustomerDetailView, TodaysNewContactsView, BulkSMSListView

urlpatterns = [
    path('',                   CustomerListView.as_view(),       name='customer-list'),
    path('todays-new/',        TodaysNewContactsView.as_view(),  name='customer-todays-new'),
    path('bulk-sms-list/',     BulkSMSListView.as_view(),        name='customer-bulk-sms'),
    path('<uuid:customer_id>/',CustomerDetailView.as_view(),     name='customer-detail'),
]
