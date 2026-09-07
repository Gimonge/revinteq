"""
Revinteq v3 — Facebook Messenger Webhook
Handles Click to Messenger ad conversations in real time.
Same Meta webhook infrastructure as WhatsApp — different event shape.

The key field is messaging[].referral which contains:
  ref:    the ad's ref parameter
  source: 'ADS'
  type:   'OPEN_THREAD'
  ad_id:  the Meta ad ID that drove the conversation

No extra Meta app review needed for Messenger — same permissions as ads_read.
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
from django.utils import timezone

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class MessengerWebhookView(View):
    """
    GET  /api/v1/messenger/webhook/ — Meta webhook verification
    POST /api/v1/messenger/webhook/ — Incoming Messenger events
    """

    def get(self, request):
        mode      = request.GET.get('hub.mode')
        token     = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        verify_token = getattr(settings, 'WHATSAPP_WEBHOOK_VERIFY_TOKEN', '')

        if mode == 'subscribe' and token == verify_token:
            logger.info("Messenger webhook verified by Meta")
            return HttpResponse(challenge, content_type='text/plain', status=200)
        return HttpResponse('Forbidden', status=403)

    def post(self, request):
        if not self._verify_signature(request):
            return HttpResponse('Forbidden', status=403)

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse('Bad Request', status=400)

        from .tasks import process_messenger_webhook
        process_messenger_webhook.delay(payload)
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
