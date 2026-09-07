from django.urls import path
from .views import SendSMSView, SMSHistoryView, SMSTriggerListView, SMSConfigAdminView, SMSConfigView, SMSMessagesView

urlpatterns = [
    path('send/',                           SendSMSView.as_view(),          name='sms-send'),
    path('messages/',                       SMSMessagesView.as_view(),      name='sms-messages'),
    path('history/',                        SMSHistoryView.as_view(),       name='sms-history'),
    path('triggers/',                       SMSTriggerListView.as_view(),   name='sms-triggers'),
    path('config/',                         SMSConfigView.as_view(),        name='sms-config'),
    path('admin/config/<uuid:tenant_id>/',  SMSConfigAdminView.as_view(),   name='sms-admin-config'),
]
