"""
Revinteq v3 — Instagram DM Webhook
Handles Click to Instagram DM ad conversations.

IMPORTANT: Requires 'instagram_manage_messages' Advanced Access from Meta.
  - Go to developers.facebook.com → Your App → App Review → Permissions
  - Request: instagram_manage_messages
  - Meta will review your app (1–4 weeks)
  - Once approved, subscribe to: messages, messaging_referrals

The referral object for Instagram DMs contains:
  ref:    ad reference parameter
  source: 'ADS'
  type:   'OPEN_THREAD'
  ad_id:  the Meta ad ID

This file is built and ready. Activate by subscribing the webhook
in Meta App Dashboard → Instagram → Webhooks → messages, messaging_referrals.
"""
import hashlib
import hmac
import json
import logging
from django.conf import settings
from django.http import HttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class InstagramWebhookView(View):
    """
    GET  /api/v1/instagram/webhook/ — Meta webhook verification
    POST /api/v1/instagram/webhook/ — Incoming Instagram DM events
    """

    def get(self, request):
        mode      = request.GET.get('hub.mode')
        token     = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        verify_token = getattr(settings, 'WHATSAPP_WEBHOOK_VERIFY_TOKEN', '')

        if mode == 'subscribe' and token == verify_token:
            logger.info("Instagram DM webhook verified by Meta")
            return HttpResponse(challenge, content_type='text/plain', status=200)
        return HttpResponse('Forbidden', status=403)

    def post(self, request):
        if not self._verify_signature(request):
            return HttpResponse('Forbidden', status=403)

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse('Bad Request', status=400)

        from .tasks import process_instagram_webhook
        process_instagram_webhook.delay(payload)
        return HttpResponse('EVENT_RECEIVED', status=200)

    def _verify_signature(self, request) -> bool:
        app_secret = getattr(settings, 'META_APP_SECRET', '')
        if not app_secret:
            return True
        signature = request.headers.get('X-Hub-Signature-256', '')
        if not signature.startswith('sha256='):
            return False
        expected = hmac.new(
            app_secret.encode(), request.body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)
