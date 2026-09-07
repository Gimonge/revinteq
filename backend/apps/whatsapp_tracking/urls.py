from django.urls import path
from .webhook import WhatsAppWebhookView
from .messenger_webhook import MessengerWebhookView
from .instagram_webhook import InstagramWebhookView
from .views import WhatsAppClickStatsView

urlpatterns = [
    path('webhook/',           WhatsAppWebhookView.as_view(),    name='whatsapp-webhook'),
    path('messenger/webhook/', MessengerWebhookView.as_view(),   name='messenger-webhook'),
    path('instagram/webhook/', InstagramWebhookView.as_view(),   name='instagram-webhook'),
    path('stats/',             WhatsAppClickStatsView.as_view(), name='whatsapp-stats'),
]
