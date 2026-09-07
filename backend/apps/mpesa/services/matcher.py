"""
Revinteq v3 — M-Pesa Transaction Matcher v2
When a Daraja C2B callback arrives, this service:
  1. Matches using the unique REV-XXX bill reference (primary — exact)
  2. Falls back to phone number match
  3. Falls back to amount + recency match (low confidence — flagged)
  4. If no match → marks unmatched for manual review
  
The bill reference system is the key innovation:
  - Every PipelineDeal gets a unique REV-XXX reference at creation
  - Business owner sends "Pay to Till 5503721, Ref REV-A3K" to customer
  - Customer types REV-A3K in M-Pesa account/reference field
  - Safaricom echoes it back in BillRefNumber
  - We do an exact lookup — no guessing, no ambiguity
"""
import logging
from decimal import Decimal
from django.utils import timezone
from apps.mpesa.models import MPesaTransaction
from apps.pipeline.models import PipelineDeal
from apps.sales.models import Sale

logger = logging.getLogger(__name__)

OPEN_STAGES = ['new_click', 'contacted', 'interested', 'negotiating']


class MPesaTransactionMatcher:
    """
    Matches an MPesaTransaction to an open PipelineDeal.

    Confidence levels:
    HIGH   — exact REV-XXX bill reference match
    MEDIUM — phone number match on open deal within 48h
    LOW    — amount + recency match (flagged for review)
    NONE   — unmatched, manual review required
    """

    AMOUNT_TOLERANCE = Decimal('0.10')  # 10% tolerance for fallback amount matching
    PHONE_WINDOW_HOURS = 48             # Phone match only within this window
    AMOUNT_WINDOW_HOURS = 24            # Amount match only within this window

    def __init__(self, transaction: MPesaTransaction):
        self.transaction = transaction
        self.tenant      = transaction.tenant

    def match_and_process(self) -> dict:
        """Main entry point. Try each matching strategy in order."""

        # ── Strategy 1: Exact bill reference (REV-XXX) ────────
        deal, confidence = self._match_by_reference()

        # ── Strategy 2: Phone number ───────────────────────────
        if not deal:
            deal, confidence = self._match_by_phone()

        # ── Strategy 3: Amount + recency ──────────────────────
        if not deal:
            deal, confidence = self._match_by_amount()

        if not deal:
            return self._mark_unmatched()

        return self._process_match(deal, confidence)

    # ── Matching strategies ────────────────────────────────────

    def _match_by_reference(self):
        """
        Exact match on BillRefNumber → PipelineDeal.mpesa_reference.
        Most reliable. Customer typed our exact reference.
        """
        bill_ref = (self.transaction.bill_ref_number or '').strip().upper()
        if not bill_ref.startswith('REV-'):
            return None, None

        try:
            deal = PipelineDeal.objects.get(
                tenant=self.tenant,
                mpesa_reference=bill_ref,
                stage__in=OPEN_STAGES,
            )
            logger.info(
                f"MATCH [HIGH] transaction {self.transaction.transaction_id} "
                f"→ deal {deal.id} via reference {bill_ref}"
            )
            return deal, 'high'
        except PipelineDeal.DoesNotExist:
            # Reference not found in open deals — may already be Won or wrong tenant
            logger.warning(
                f"Reference {bill_ref} not found in open deals "
                f"for tenant {self.tenant.name}"
            )
            return None, None

    def _match_by_phone(self):
        """
        Match by customer phone number on deals created in last 48 hours.
        Medium confidence — phone could belong to multiple deals.
        """
        phone = (self.transaction.msisdn or '').strip()
        if not phone:
            return None, None

        # Normalise phone (remove leading + or 0, ensure 254 prefix)
        phone_norm = phone.lstrip('+')
        if phone_norm.startswith('0'):
            phone_norm = '254' + phone_norm[1:]

        cutoff = timezone.now() - timezone.timedelta(hours=self.PHONE_WINDOW_HOURS)

        deals = PipelineDeal.objects.filter(
            tenant=self.tenant,
            stage__in=OPEN_STAGES,
            created_at__gte=cutoff,
        ).filter(
            customer_phone__in=[phone, '+' + phone, phone_norm, '+' + phone_norm]
        ).order_by('-created_at')

        if deals.count() == 1:
            deal = deals.first()
            logger.info(
                f"MATCH [MEDIUM] transaction {self.transaction.transaction_id} "
                f"→ deal {deal.id} via phone {phone}"
            )
            return deal, 'medium'
        elif deals.count() > 1:
            # Multiple phone matches — pick most recent but flag for review
            deal = deals.first()
            logger.warning(
                f"MATCH [MEDIUM/AMBIGUOUS] {deals.count()} deals match phone {phone} "
                f"— using most recent: {deal.id}"
            )
            return deal, 'medium_ambiguous'

        return None, None

    def _match_by_amount(self):
        """
        Match by amount within tolerance on deals created in last 24 hours.
        Low confidence — only used as last resort before unmatched.
        Always flagged for manual review.
        """
        amount = self.transaction.amount
        if not amount:
            return None, None

        lower = amount * (1 - self.AMOUNT_TOLERANCE)
        upper = amount * (1 + self.AMOUNT_TOLERANCE)
        cutoff = timezone.now() - timezone.timedelta(hours=self.AMOUNT_WINDOW_HOURS)

        deals = PipelineDeal.objects.filter(
            tenant=self.tenant,
            stage__in=OPEN_STAGES,
            estimated_value__range=(lower, upper),
            created_at__gte=cutoff,
        ).order_by('-created_at')

        if deals.count() == 1:
            deal = deals.first()
            logger.warning(
                f"MATCH [LOW] transaction {self.transaction.transaction_id} "
                f"→ deal {deal.id} via amount {amount} (needs review)"
            )
            return deal, 'low'

        return None, None

    # ── Process a confirmed match ──────────────────────────────

    def _process_match(self, deal: PipelineDeal, confidence: str) -> dict:
        """Auto-log sale, mark deal Won, update stats."""
        from datetime import date

        # Create the sale record
        sale = Sale.objects.create(
            tenant          = self.tenant,
            pipeline_deal   = deal,
            ad              = deal.ad,
            campaign        = deal.campaign,
            product_name    = 'M-Pesa Auto-Payment',
            amount          = self.transaction.amount,
            payment_method  = 'mpesa_auto',
            payment_reference = self.transaction.transaction_id,
            platform_source = deal.platform,
            sale_date       = date.today(),
            is_confirmed    = True,
            notes           = f'Auto-matched from M-Pesa callback. Confidence: {confidence}. '
                              f'Sender: {self.transaction.first_name} {self.transaction.last_name}',
        )

        # Mark deal Won
        deal.advance_to_stage('won')

        # Update M-Pesa transaction
        self.transaction.status      = 'matched'
        self.transaction.matched_deal= deal
        self.transaction.matched_sale= sale
        self.transaction.match_confidence = confidence
        self.transaction.matched_at  = timezone.now()
        self.transaction.save(update_fields=[
            'status', 'matched_deal', 'matched_sale',
            'match_confidence', 'matched_at'
        ])

        # Update customer stats if linked
        if deal.customer:
            deal.customer.update_stats()

        # Fire auto-SMS confirmation
        self._fire_confirmation_sms(deal, sale)

        # Fire external webhooks
        from apps.external_api.tasks import dispatch_webhook
        dispatch_webhook.delay(
            str(self.tenant.id),
            'sale.mpesa_auto',
            {
                'transaction_id': self.transaction.transaction_id,
                'amount':         float(self.transaction.amount),
                'deal_id':        str(deal.id),
                'sale_id':        str(sale.id),
                'confidence':     confidence,
                'platform':       deal.platform,
            }
        )

        logger.info(
            f"M-Pesa auto-match SUCCESS: {self.transaction.transaction_id} "
            f"→ deal {deal.id} | confidence: {confidence} | "
            f"KES {self.transaction.amount}"
        )

        return {
            'status':         'matched',
            'confidence':     confidence,
            'transaction_id': self.transaction.transaction_id,
            'amount':         float(self.transaction.amount),
            'deal_id':        str(deal.id),
            'sale_id':        str(sale.id),
            'deal_platform':  deal.platform,
            'needs_review':   confidence in ('low', 'medium_ambiguous'),
            'message': (
                f"Payment of KES {self.transaction.amount:,.0f} auto-matched "
                f"and logged. Confidence: {confidence}."
            ),
        }

    def _mark_unmatched(self) -> dict:
        self.transaction.status = 'unmatched'
        self.transaction.save(update_fields=['status'])
        logger.warning(
            f"M-Pesa UNMATCHED: {self.transaction.transaction_id} "
            f"KES {self.transaction.amount} | Ref: {self.transaction.bill_ref_number} "
            f"for tenant {self.tenant.name}"
        )
        return {
            'status':         'unmatched',
            'transaction_id': self.transaction.transaction_id,
            'amount':         float(self.transaction.amount),
            'bill_reference': self.transaction.bill_ref_number,
            'message': (
                'No matching pipeline deal found. '
                'Please go to M-Pesa Transactions and manually link this payment.'
            ),
        }

    def _fire_confirmation_sms(self, deal: PipelineDeal, sale: Sale):
        """Send auto-SMS payment confirmation if trigger is enabled."""
        try:
            from apps.sms.tasks import send_auto_sms
            phone = deal.customer_phone or (deal.customer.phone_number if deal.customer else '')
            if not phone:
                return
            send_auto_sms.delay(
                tenant_id=str(self.tenant.id),
                trigger='mpesa_payment_received',
                context={
                    'customer_name': deal.customer_name or 'Valued Customer',
                    'phone':         phone,
                    'amount':        f"{self.tenant.currency} {sale.amount:,.0f}",
                    'transaction_id':self.transaction.transaction_id,
                    'business_name': self.tenant.name,
                }
            )
        except Exception as e:
            logger.warning(f"Auto-SMS failed after M-Pesa match: {e}")
