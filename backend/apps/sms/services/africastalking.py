"""
Revinteq v3 — Africa's Talking SMS Service
"""
import logging
import africastalking
from apps.sms.models import SMSConfig, SMSMessage

logger = logging.getLogger(__name__)


class ATSMSService:
    """Africa's Talking SMS client for one tenant."""

    def __init__(self, config: SMSConfig):
        self.config = config
        africastalking.initialize(config.username, config.api_key)
        self.sms = africastalking.SMS

    def send(
        self,
        recipient: str,
        message: str,
        sender_id: str = None,
        tenant=None,
        source: str = 'manual',
        trigger: str = '',
        sent_by=None,
        recipient_name: str = '',
    ) -> SMSMessage:
        """
        Send a single SMS and log it.
        Returns the SMSMessage record.
        """
        from django.utils import timezone

        # Normalise phone to +254XXXXXXXXX
        phone = self._normalise_phone(recipient)
        sender = sender_id or self.config.sender_id or None

        # Create log record
        log = SMSMessage.objects.create(
            tenant=tenant or self.config.tenant,
            recipient_number=phone,
            recipient_name=recipient_name,
            message=message,
            source=source,
            trigger=trigger,
            status='queued',
            sent_by=sent_by,
        )

        try:
            response = self.sms.send(
                message,
                [phone],
                sender_id=sender,
            )
            recipients = response.get('SMSMessageData', {}).get('Recipients', [])
            if recipients:
                r = recipients[0]
                log.at_message_id = r.get('messageId', '')
                log.at_status_code = r.get('statusCode', '')
                log.cost = self._parse_cost(r.get('cost', '0'))
                log.status = 'sent' if r.get('statusCode') == 101 else 'failed'
                log.sent_at = timezone.now()
            else:
                log.status = 'failed'

        except Exception as e:
            logger.exception(f"Africa's Talking send failed: {e}")
            log.status = 'failed'

        log.save()
        return log

    def send_bulk(self, recipients: list, message: str, tenant=None, sent_by=None) -> list:
        """
        Send the same message to multiple recipients.
        recipients: list of phone numbers or {'phone': '...', 'name': '...'}
        Returns list of SMSMessage records.
        """
        results = []
        for r in recipients:
            if isinstance(r, dict):
                phone = r.get('phone', '')
                name = r.get('name', '')
            else:
                phone = str(r)
                name = ''

            if not phone:
                continue

            log = self.send(
                recipient=phone,
                message=message,
                tenant=tenant,
                source='bulk',
                sent_by=sent_by,
                recipient_name=name,
            )
            results.append(log)

        return results

    @staticmethod
    def _normalise_phone(phone: str) -> str:
        p = str(phone).strip().replace(' ', '').replace('-', '')
        if p.startswith('0'):
            p = '+254' + p[1:]
        elif p.startswith('254') and not p.startswith('+'):
            p = '+' + p
        elif not p.startswith('+'):
            p = '+' + p
        return p

    @staticmethod
    def _parse_cost(cost_str: str) -> float:
        try:
            return float(str(cost_str).replace('KES ', '').replace(',', ''))
        except (ValueError, AttributeError):
            return 0.0
