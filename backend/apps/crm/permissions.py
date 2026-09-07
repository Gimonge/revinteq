from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.tokens import AccessToken
from .models import CRMUser

def get_crm_user_from_request(request):
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    try:
        token = AccessToken(auth.split(' ')[1])
        crm_user_id = token.get('crm_user_id')
        if not crm_user_id:
            return None
        return CRMUser.objects.get(id=crm_user_id, is_active=True)
    except Exception:
        return None

class IsCRMUser(BasePermission):
    def has_permission(self, request, view):
        crm_user = get_crm_user_from_request(request)
        if crm_user:
            request.crm_user = crm_user
            return True
        return False
