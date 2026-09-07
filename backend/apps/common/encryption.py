"""
Revinteq v3 — Field Encryption
Replaces django-cryptography (incompatible with Django 5) with a simple
encrypt/decrypt wrapper using Python's cryptography library + Fernet.

Usage in models:
    from apps.common.encryption import EncryptedTextField, EncryptedCharField
    access_token = EncryptedTextField()
    consumer_key = EncryptedCharField(max_length=200)
"""
import base64
import logging
from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)

# ── Key derivation ────────────────────────────────────────────
def _get_fernet():
    """Get a Fernet instance using the FIELD_ENCRYPTION_KEY setting."""
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        raise RuntimeError(
            "cryptography package is required for field encryption. "
            "Run: pip install cryptography"
        )

    raw_key = getattr(settings, 'FIELD_ENCRYPTION_KEY', '')
    if not raw_key:
        raise ValueError("FIELD_ENCRYPTION_KEY is not set in settings.")

    # Fernet needs exactly 32 url-safe base64-encoded bytes
    # Pad or truncate the key to 32 bytes then encode
    key_bytes = raw_key.encode()[:32].ljust(32, b'0')
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def encrypt_value(value: str) -> str:
    """Encrypt a string value. Returns empty string for empty input."""
    if not value:
        return value
    f = _get_fernet()
    return f.encrypt(value.encode()).decode()


def decrypt_value(value: str) -> str:
    """Decrypt an encrypted string. Returns the value as-is if not encrypted."""
    if not value:
        return value
    try:
        f = _get_fernet()
        return f.decrypt(value.encode()).decode()
    except Exception:
        # If decryption fails the value may already be plaintext (migration scenario)
        return value


# ── Custom model fields ───────────────────────────────────────

class EncryptedMixin:
    """Mixin that transparently encrypts on save and decrypts on load."""

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt_value(value)

    def to_python(self, value):
        if value is None:
            return value
        # If it already looks decrypted (no gAAAAAB prefix) return as-is
        if not value.startswith('gAAAAAB'):
            return value
        return decrypt_value(value)

    def get_prep_value(self, value):
        if value is None:
            return value
        # Don't double-encrypt
        if value.startswith('gAAAAAB'):
            return value
        return encrypt_value(value)


class EncryptedCharField(EncryptedMixin, models.CharField):
    """CharField with transparent Fernet encryption."""
    pass


class EncryptedTextField(EncryptedMixin, models.TextField):
    """TextField with transparent Fernet encryption."""
    pass


# ── Drop-in replacement for django_cryptography.fields.encrypt ──
def encrypt(field):
    """
    Drop-in replacement for django_cryptography's encrypt() wrapper.
    Returns an encrypted version of any CharField or TextField.

    Usage:
        from apps.common.encryption import encrypt
        api_key = encrypt(models.CharField(max_length=200))
    """
    if isinstance(field, models.TextField):
        new_field = EncryptedTextField(
            blank=field.blank,
            null=field.null,
            default=field.default if field.default is not models.fields.NOT_PROVIDED else '',
        )
    else:
        # Default to EncryptedCharField
        new_field = EncryptedCharField(
            max_length=getattr(field, 'max_length', 500),
            blank=field.blank,
            null=field.null,
            default=field.default if field.default is not models.fields.NOT_PROVIDED else '',
        )
    return new_field
