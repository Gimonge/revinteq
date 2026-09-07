"""
Revinteq v3 — WhatsApp Business API Webhook
Receives real-time events from Meta when a customer sends a WhatsApp
message that originated from a Facebook or Instagram ad.

The key field is message.referral which contains:
  - source_id:   the Meta ad ID
  - source_type: 'ad' or 'post'
  - source_url:  the ad URL
  - headline:    the ad headline

When we receive a message with a referral, we:
  1. Find the Ad record by meta_ad_id
  2. Create a PipelineDeal at 'new_click' stage
  3. Store the whatsapp_message_id for dedup
  4. Fire external webhooks
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
class WhatsAppWebhookView(View):
    """
    GET  /api/v1/whatsapp/webhook/  — Meta webhook verification
    POST /api/v1/whatsapp/webhook/  — Incoming message events
    """

    # ── Webhook Verification (Meta calls this once to verify) ──
    def get(self, request):
        """
        Meta sends a GET with:
          hub.mode = 'subscribe'
          hub.verify_token = your configured verify token
          hub.challenge = a random string to echo back
        """
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')

        verify_token = getattr(settings, 'WHATSAPP_WEBHOOK_VERIFY_TOKEN', '')

        if mode == 'subscribe' and token == verify_token:
            logger.info("WhatsApp webhook verified by Meta")
            return HttpResponse(challenge, content_type='text/plain', status=200)

        logger.warning(
            f"WhatsApp webhook verification failed. "
            f"Token received: {token}"
        )
        return HttpResponse('Forbidden', status=403)

    # ── Incoming Events ───────────────────────────────────────
    def post(self, request):
        """
        Meta POSTs message events here in real time.
        We only care about messages that have a .referral object
        (meaning the customer came from an ad).
        """
        # Verify the payload signature
        if not self._verify_signature(request):
            logger.warning("WhatsApp webhook: invalid signature")
            return HttpResponse('Forbidden', status=403)

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse('Bad Request', status=400)

        # Process asynchronously to return 200 to Meta immediately
        from .tasks import process_whatsapp_webhook
        process_whatsapp_webhook.delay(payload)

        # Meta requires a 200 response within 20 seconds
        return HttpResponse('EVENT_RECEIVED', status=200)

    def _verify_signature(self, request) -> bool:
        """
        Verify the X-Hub-Signature-256 header using the app secret.
        This ensures the request genuinely came from Meta.
        """
        app_secret = getattr(settings, 'META_APP_SECRET', '')
        if not app_secret:
            return True  # Skip verification if not configured (dev only)

        signature = request.headers.get('X-Hub-Signature-256', '')
        if not signature.startswith('sha256='):
            return False

        expected = hmac.new(
            app_secret.encode(), request.body, hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(f"sha256={expected}", signature)
