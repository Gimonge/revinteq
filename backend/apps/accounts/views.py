"""Revinteq v3 — Accounts Views"""
import logging
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from apps.tenants.models import Tenant, TenantUser
from .models import UserProfile

logger = logging.getLogger(__name__)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from django.contrib.auth import authenticate

        email    = request.data.get('email', request.data.get('username', '')).lower().strip()
        password = request.data.get('password', '')

        if not email or not password:
            return Response({'error': True, 'message': 'Email and password are required.'}, status=400)

        # Step 1: find the user by email OR username
        user_obj = None
        try:
            user_obj = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Try username match as fallback
            try:
                user_obj = User.objects.get(username__iexact=email)
            except User.DoesNotExist:
                pass
        except User.MultipleObjectsReturned:
            # Multiple accounts with same email — try username match
            try:
                user_obj = User.objects.get(username__iexact=email)
            except User.DoesNotExist:
                user_obj = User.objects.filter(email__iexact=email).first()

        if not user_obj:
            return Response({'error': True, 'message': 'Invalid email or password.'}, status=401)

        # Step 2: authenticate using the actual username
        user = authenticate(request, username=user_obj.username, password=password)

        if not user:
            return Response({'error': True, 'message': 'Invalid email or password.'}, status=401)

        if not user.is_active:
            return Response({'error': True, 'message': 'Account is disabled.'}, status=401)

        refresh    = RefreshToken.for_user(user)
        membership = TenantUser.objects.filter(user=user, is_active=True).first()
        tenant_data = None

        if membership:
            t = membership.tenant
            tenant_data = {
                'id':   str(t.id),
                'name': t.name,
                'slug': t.slug,
                'currency': t.currency,
                'status':   t.status,
                'budget_increase_cap_percent': t.budget_increase_cap_percent,
                'meta_fb_connected':   t.meta_fb_connected,
                'meta_ig_connected':   t.meta_ig_connected,
                'onboarding_complete': t.onboarding_complete,
                'whatsapp_number':     t.whatsapp_number,
            }

        logger.info(f"Login success: {user.email or user.username} | role: {membership.role if membership else 'none'}")

        return Response({
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id':    user.id,
                'email': user.email or user.username,
                'name':  (f"{user.first_name} {user.last_name}").strip() or user.email or user.username,
                'role':  membership.role if membership else 'SUPER_ADMIN' if user.is_superuser else None,
            },
            'tenant': tenant_data,
        })


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email    = request.data.get('email', '').lower().strip()
        password = request.data.get('password', '')
        name     = request.data.get('full_name', '')
        if not email or not password:
            return Response({'error': True, 'message': 'Email and password are required.'}, status=400)
        if User.objects.filter(email=email).exists():
            return Response({'error': True, 'message': 'Email already registered.'}, status=400)
        names = name.split(' ', 1)
        user  = User.objects.create_user(
            username=email, email=email, password=password,
            first_name=names[0] if names else '',
            last_name=names[1] if len(names) > 1 else '',
        )
        UserProfile.objects.create(user=user, full_name=name)
        refresh = RefreshToken.for_user(user)
        return Response({
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
            'user':    {'id': user.id, 'email': user.email},
        }, status=201)


class AccountDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.tenants.models import TenantUser
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Always do fresh DB lookup by user ID — never trust middleware for JWT
        try:
            user = User.objects.get(pk=request.user.pk)
        except User.DoesNotExist:
            return Response({'error': True, 'message': 'User not found.'}, status=404)

        tu = TenantUser.objects.select_related('tenant').filter(
            user__pk=user.pk, is_active=True
        ).first()

        tenant = tu.tenant if tu else None
        tenant_data = None
        if tenant:
            tenant_data = {
                'id':                        str(tenant.id),
                'name':                      tenant.name,
                'slug':                      tenant.slug,
                'currency':                  tenant.currency,
                'status':                    tenant.status,
                'budget_increase_cap_percent': tenant.budget_increase_cap_percent,
                'meta_fb_connected':         tenant.meta_fb_connected,
                'meta_ig_connected':         tenant.meta_ig_connected,
                'onboarding_complete':       tenant.onboarding_complete,
                'whatsapp_number':           tenant.whatsapp_number,
            }

        return Response({
            'id':              user.pk,
            'email':           user.email or user.username,
            'name':            (f"{user.first_name} {user.last_name}").strip() or user.email or user.username,
            'role':            tu.role if tu else ('SUPER_ADMIN' if user.is_superuser else None),
            'is_impersonating': getattr(request, 'is_impersonating', False),
            'tenant':          tenant_data,
        })


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_pw = request.data.get('old_password', '')
        new_pw = request.data.get('new_password', '')
        if not request.user.check_password(old_pw):
            return Response({'error': True, 'message': 'Old password is incorrect.'}, status=400)
        if len(new_pw) < 8:
            return Response({'error': True, 'message': 'Password must be at least 8 characters.'}, status=400)
        request.user.set_password(new_pw)
        request.user.save()
        return Response({'message': 'Password changed.'})


class OnboardingCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return Response({'error': True, 'message': 'No tenant.'}, status=400)
        wa = request.data.get('whatsapp_number', '')
        if wa:
            tenant.whatsapp_number          = wa
            tenant.whatsapp_default_message = request.data.get('whatsapp_default_message', '')
        tenant.onboarding_complete = True
        tenant.save()
        return Response({'message': 'Onboarding complete!'})
