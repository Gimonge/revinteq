"""
Revinteq v3 — Daraja API Client
Handles M-Pesa C2B registration and STK Push via Safaricom Daraja API.
"""
import base64
import logging
import requests
from datetime import datetime
from django.utils import timezone
from apps.mpesa.models import MPesaConfig

logger = logging.getLogger(__name__)


class DarajaClient:
    """
    Safaricom Daraja API client for one tenant's M-Pesa config.
    Supports: C2B URL registration, token generation.
    """

    def __init__(self, config: MPesaConfig):
        self.config = config
        self.base_url = config.base_url
        self._access_token = None

    def get_access_token(self) -> str:
        """
        Generate a Daraja OAuth access token.
        Token is valid for 1 hour — Daraja requires fresh token per session.
        """
        credentials = base64.b64encode(
            f"{self.config.consumer_key}:{self.config.consumer_secret}".encode()
        ).decode()

        response = requests.get(
            f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials",
            headers={'Authorization': f'Basic {credentials}'},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        token = data.get('access_token')
        if not token:
            raise DarajaError("Could not retrieve access token from Daraja")
        self._access_token = token
        return token

    def _get_headers(self) -> dict:
        if not self._access_token:
            self.get_access_token()
        return {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/json',
        }

    def register_c2b_urls(
        self,
        confirmation_url: str,
        validation_url: str,
    ) -> dict:
        """
        Register the C2B callback URLs with Safaricom.
        Must be called once when setting up a new tenant's M-Pesa config.
        Safaricom will POST to these URLs when payments come in.

        confirmation_url: URL Safaricom POSTs confirmed payments to
        validation_url:   URL Safaricom POSTs for validation (can return Accept/Reject)
        """
        payload = {
            "ShortCode": self.config.shortcode,
            "ResponseType": "Completed",
            "ConfirmationURL": confirmation_url,
            "ValidationURL": validation_url,
        }

        response = requests.post(
            f"{self.base_url}/mpesa/c2b/v1/registerurl",
            json=payload,
            headers=self._get_headers(),
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        logger.info(
            f"C2B URLs registered for {self.config.tenant.name}: "
            f"confirmation={confirmation_url}"
        )
        return data

    def stk_push(
        self,
        phone_number: str,
        amount: int,
        account_reference: str,
        transaction_desc: str,
        callback_url: str,
    ) -> dict:
        """
        Initiate an STK Push (Lipa na M-Pesa Online) payment request.
        Sends a payment prompt to the customer's phone.
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(
            f"{self.config.shortcode}{self.config.passkey}{timestamp}".encode()
        ).decode()

        # Normalize phone number to 254XXXXXXXXX format
        phone = str(phone_number).strip()
        if phone.startswith('+'):
            phone = phone[1:]
        if phone.startswith('0'):
            phone = '254' + phone[1:]

        payload = {
            "BusinessShortCode": self.config.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline"
                if self.config.shortcode_type == 'paybill'
                else "CustomerBuyGoodsOnline",
            "Amount": int(amount),
            "PartyA": phone,
            "PartyB": self.config.shortcode,
            "PhoneNumber": phone,
            "CallBackURL": callback_url,
            "AccountReference": account_reference[:12],
            "TransactionDesc": transaction_desc[:13],
        }

        response = requests.post(
            f"{self.base_url}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers=self._get_headers(),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


class DarajaError(Exception):
    pass
