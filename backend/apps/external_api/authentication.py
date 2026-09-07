"""
Revinteq v3 — External API Authentication
Kept in its own file so it can be safely referenced in
DEFAULT_AUTHENTICATION_CLASSES without triggering circular imports.
"""
import logging
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)


class APIKeyAuthentication(BaseAuthentication):
    """
    Authenticate requests using the Api-Key header.
    Header format: Authorization: Api-Key rvq_live_XXXXXXXX
    Used by POS systems and third-party integrations.
    """

    def authenticate(self, request):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Api-Key '):
            return None

        key_value = auth.split('Api-Key ', 1)[1].strip()

        # Lazy import to avoid circular imports at module load time
        from apps.external_api.models import ExternalAPIKey

        try:
            api_key = ExternalAPIKey.objects.select_related('tenant').get(
                key=key_value, is_active=True
            )
        except ExternalAPIKey.DoesNotExist:
            raise AuthenticationFailed('Invalid or revoked API key.')

        # Update last used timestamp
        ExternalAPIKey.objects.filter(pk=api_key.pk).update(
            last_used_at=timezone.now()
        )

        # Attach tenant to request
        request.tenant    = api_key.tenant
        request.api_key   = api_key
        request.tenant_user = None

        return (api_key, None)

    def authenticate_header(self, request):
        return 'Api-Key'
