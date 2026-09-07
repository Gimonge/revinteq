"""
Revinteq v3 — Tenant Management Views
Admin-only: create tenants, invite clients, impersonate tenants.
"""
import secrets
import logging
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import (
    ModelSerializer, Serializer, CharField,
    EmailField, ChoiceField, UUIDField, SerializerMethodField
)
from .models import Tenant, TenantUser, TenantInvitation
from .permissions import IsSuperAdmin, IsAdminOrSuperAdmin

logger = logging.getLogger(__name__)


# ── Serializers ───────────────────────────────────────────────

class TenantSerializer(ModelSerializer):
    member_count    = SerializerMethodField()
    monthly_revenue      = SerializerMethodField()
    open_deals           = SerializerMethodField()
    last_sale            = SerializerMethodField()
    sales_count          = SerializerMethodField()
    ad_spend             = SerializerMethodField()
    roi                  = SerializerMethodField()
    aov                  = SerializerMethodField()
    conv_rate            = SerializerMethodField()
    monthly_goal         = SerializerMethodField()
    goal_progress        = SerializerMethodField()
    goal_status          = SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'status', 'currency',
            'contact_name', 'contact_email', 'contact_phone',
            'whatsapp_number', 'industry', 'location',
            'budget_increase_cap_percent',
            'meta_fb_connected', 'meta_ig_connected',
            'onboarding_complete', 'notes',
            'member_count', 'created_at',
            'monthly_revenue', 'open_deals', 'last_sale',
            'sales_count', 'ad_spend', 'roi', 'aov', 'conv_rate',
            'monthly_goal', 'goal_progress', 'goal_status',
        ]
        read_only_fields = ['id', 'created_at', 'member_count']

    def get_member_count(self, obj):
        return obj.memberships.filter(is_active=True).count()

    def _month_sales(self, obj):
        """Cache month sales queryset per tenant."""
        if not hasattr(self, '_sales_cache'):
            self._sales_cache = {}
        if obj.id not in self._sales_cache:
            from apps.sales.models import Sale
            from django.utils import timezone
            from django.db.models import Sum, Count, Avg
            today = timezone.now().date()
            month_start = today.replace(day=1)
            qs = Sale.objects.filter(tenant=obj, sale_date__gte=month_start)
            agg = qs.aggregate(total=Sum('amount'), count=Count('id'), avg=Avg('amount'))
            self._sales_cache[obj.id] = agg
        return self._sales_cache[obj.id]

    def get_monthly_revenue(self, obj):
        agg = self._month_sales(obj)
        return float(agg.get('total') or 0)

    def get_sales_count(self, obj):
        agg = self._month_sales(obj)
        return agg.get('count') or 0

    def get_aov(self, obj):
        agg = self._month_sales(obj)
        return float(agg.get('avg') or 0)

    def get_open_deals(self, obj):
        try:
            from apps.pipeline.models import PipelineDeal
            return PipelineDeal.objects.filter(
                tenant=obj,
                stage__in=['new_click', 'contacted', 'interested', 'negotiating']
            ).count()
        except Exception:
            return 0

    def get_last_sale(self, obj):
        try:
            from apps.sales.models import Sale
            from django.utils import timezone
            sale = Sale.objects.filter(tenant=obj).order_by('-sale_date').first()
            if not sale:
                return None
            today = timezone.now().date()
            delta = (today - sale.sale_date).days
            if delta == 0:
                return 'Today'
            elif delta == 1:
                return 'Yesterday'
            elif delta < 7:
                return f'{delta} days ago'
            return sale.sale_date.strftime('%d %b %Y')
        except Exception:
            return None

    def get_ad_spend(self, obj):
        try:
            from apps.metrics.models import MetricSnapshot
            from django.utils import timezone
            snap = MetricSnapshot.objects.filter(
                tenant=obj, period_type='month'
            ).order_by('-period_start').first()
            return float(snap.total_spend or 0) if snap else 0
        except Exception:
            return 0

    def get_roi(self, obj):
        revenue = self.get_monthly_revenue(obj)
        spend   = self.get_ad_spend(obj)
        if spend > 0 and revenue > 0:
            return round(((revenue - spend) / spend) * 100, 1)
        return 0

    def get_conv_rate(self, obj):
        try:
            from apps.pipeline.models import PipelineDeal
            total = PipelineDeal.objects.filter(tenant=obj).count()
            won   = PipelineDeal.objects.filter(tenant=obj, stage='won').count()
            return round((won / total) * 100, 1) if total > 0 else 0
        except Exception:
            return 0

    def get_monthly_goal(self, obj):
        try:
            from apps.revenue_goals.models import RevenueGoal
            from django.utils import timezone
            today = timezone.now().date().replace(day=1)
            goal = RevenueGoal.objects.filter(tenant=obj, month=today).first()
            return float(goal.target_amount) if goal else None
        except Exception:
            return None

    def get_goal_progress(self, obj):
        try:
            monthly_goal = self.get_monthly_goal(obj)
            if not monthly_goal:
                return 0
            monthly_revenue = self.get_monthly_revenue(obj)
            return min(round((monthly_revenue / monthly_goal) * 100, 1), 100)
        except Exception:
            return 0

    def get_goal_status(self, obj):
        try:
            monthly_goal = self.get_monthly_goal(obj)
            if not monthly_goal:
                return 'no_goal'
            progress = self.get_goal_progress(obj)
            revenue  = self.get_monthly_revenue(obj)
            if revenue >= monthly_goal:
                return 'ahead'
            elif progress >= 60:
                return 'on_track'
            else:
                return 'behind'
        except Exception:
            return 'no_goal'


class TenantCreateSerializer(Serializer):
    # Tenant fields
    name          = CharField(max_length=200)
    contact_name  = CharField(max_length=200, required=False, allow_blank=True)
    contact_email = EmailField(required=False, allow_blank=True)
    contact_phone = CharField(max_length=20,  required=False, allow_blank=True)
    currency      = ChoiceField(choices=['KES','UGX','TZS','USD','GBP'], default='KES')
    industry      = CharField(max_length=100, required=False, allow_blank=True)
    location      = CharField(max_length=200, required=False, allow_blank=True)
    notes         = CharField(required=False, allow_blank=True)
    # Client login credentials (optional — admin can set them at creation time)
    client_email    = EmailField(required=False, allow_blank=True)
    client_password = CharField(max_length=128, required=False, allow_blank=True)

    def create(self, validated_data):
        from django.utils.text import slugify

        # Pop credential fields before creating tenant
        client_email    = validated_data.pop('client_email', '').strip()
        client_password = validated_data.pop('client_password', '').strip()

        # Build a unique slug
        base_slug = slugify(validated_data['name'])
        slug = base_slug
        counter = 1
        while Tenant.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        tenant = Tenant.objects.create(
            slug=slug,
            created_by=self.context['request'].user,
            meta_fb_access_token='',
            meta_fb_connected=False,
            meta_ig_connected=False,
            onboarding_complete=False,
            **validated_data,
        )

        # If admin provided credentials, create the client user immediately
        if client_email and client_password:
            # Reuse existing user if email already exists
            user, created = User.objects.get_or_create(
                email=client_email,
                defaults={
                    'username': client_email,
                    'first_name': validated_data.get('contact_name', '').split()[0] if validated_data.get('contact_name') else '',
                }
            )
            if created or client_password:
                user.set_password(client_password)
                user.save()

            # Link user to tenant as CLIENT
            tu, created = TenantUser.objects.get_or_create(
                user=user,
                tenant=tenant,
                defaults={'role': 'CLIENT', 'is_active': True},
            )
            # Ensure is_active is True even if record already existed
            if not tu.is_active:
                tu.is_active = True
                tu.save(update_fields=['is_active'])

        return tenant


class InviteClientSerializer(Serializer):
    email = EmailField()
    role = ChoiceField(choices=['CLIENT', 'ADMIN'], default='CLIENT')


class TenantUserSerializer(ModelSerializer):
    user_email = CharField(source='user.email', read_only=True)
    user_name = SerializerMethodField()
    tenant_name = CharField(source='tenant.name', read_only=True)

    class Meta:
        model = TenantUser
        fields = [
            'id', 'user_email', 'user_name', 'tenant_name',
            'role', 'is_active', 'joined_at',
        ]

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email


# ── Views ─────────────────────────────────────────────────────

class TenantListCreateView(APIView):
    """
    GET  /api/v1/admin/tenants/        — list all tenants
    POST /api/v1/admin/tenants/        — create new tenant
    """
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):
        tenants = Tenant.objects.prefetch_related('memberships').order_by('name')
        status_filter = request.query_params.get('status')
        if status_filter:
            tenants = tenants.filter(status=status_filter)
        return Response(TenantSerializer(tenants, many=True).data)

    def post(self, request):
        serializer = TenantCreateSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        tenant = serializer.save()
        logger.info(f"Tenant created: {tenant.name} by {request.user.email}")
        return Response(TenantSerializer(tenant).data, status=status.HTTP_201_CREATED)


class TenantDetailView(APIView):
    """
    GET   /api/v1/admin/tenants/<id>/   — retrieve
    PATCH /api/v1/admin/tenants/<id>/   — update
    """
    permission_classes = [IsAdminOrSuperAdmin]

    def _get_tenant(self, tenant_id):
        try:
            return Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return None

    def get(self, request, tenant_id):
        tenant = self._get_tenant(tenant_id)
        if not tenant:
            return Response({'error': True, 'message': 'Tenant not found.'}, status=404)
        return Response(TenantSerializer(tenant).data)

    def patch(self, request, tenant_id):
        tenant = self._get_tenant(tenant_id)
        if not tenant:
            return Response({'error': True, 'message': 'Tenant not found.'}, status=404)
        serializer = TenantSerializer(tenant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class InviteClientView(APIView):
    """
    POST /api/v1/admin/tenants/<id>/invite/
    Send an invitation to a client to join their portal.
    """
    permission_classes = [IsAdminOrSuperAdmin]

    def post(self, request, tenant_id):
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return Response({'error': True, 'message': 'Tenant not found.'}, status=404)

        serializer = InviteClientSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        role = serializer.validated_data['role']

        # Check if user already exists
        existing_user = User.objects.filter(email=email).first()
        if existing_user:
            # Add to tenant directly
            membership, created = TenantUser.objects.get_or_create(
                user=existing_user,
                tenant=tenant,
                defaults={'role': role, 'invited_by': request.user}
            )
            if not created:
                return Response({
                    'error': True,
                    'message': f'{email} already has access to {tenant.name}.'
                }, status=400)

            return Response({
                'message': f'{email} added to {tenant.name} as {role}.',
                'type': 'existing_user'
            })

        # Create invitation token
        token = secrets.token_urlsafe(48)
        invitation = TenantInvitation.objects.create(
            tenant=tenant,
            email=email,
            role=role,
            token=token,
            invited_by=request.user,
            expires_at=timezone.now() + timedelta(days=7),
        )

        # TODO: Send invitation email with token link
        # For now, return the token in response (admin shares manually)
        invite_url = f"{request.build_absolute_uri('/').rstrip('/')}"\
                     f"/client/accept-invite/{token}/"

        logger.info(f"Invitation created for {email} → {tenant.name}")
        return Response({
            'message': f'Invitation created for {email}.',
            'invite_url': invite_url,
            'expires_at': invitation.expires_at,
            'type': 'new_invitation',
        }, status=status.HTTP_201_CREATED)


class AcceptInvitationView(APIView):
    """
    POST /api/v1/auth/accept-invite/
    Client sets their password and activates their account.
    """
    permission_classes = []  # Public

    def post(self, request):
        token = request.data.get('token')
        password = request.data.get('password')
        full_name = request.data.get('full_name', '')

        if not token or not password:
            return Response(
                {'error': True, 'message': 'Token and password are required.'},
                status=400
            )

        try:
            invitation = TenantInvitation.objects.get(
                token=token, status='pending'
            )
        except TenantInvitation.DoesNotExist:
            return Response(
                {'error': True, 'message': 'Invalid or expired invitation.'},
                status=400
            )

        if invitation.expires_at < timezone.now():
            invitation.status = 'expired'
            invitation.save()
            return Response(
                {'error': True, 'message': 'This invitation has expired. Please request a new one.'},
                status=400
            )

        # Create user
        names = full_name.split(' ', 1)
        user = User.objects.create_user(
            username=invitation.email,
            email=invitation.email,
            password=password,
            first_name=names[0] if names else '',
            last_name=names[1] if len(names) > 1 else '',
        )

        # Link to tenant
        TenantUser.objects.create(
            user=user,
            tenant=invitation.tenant,
            role=invitation.role,
            invited_by=invitation.invited_by,
        )

        # Mark invitation accepted
        invitation.status = 'accepted'
        invitation.accepted_at = timezone.now()
        invitation.save()

        # Issue JWT tokens
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)

        logger.info(f"Invitation accepted: {user.email} → {invitation.tenant.name}")
        return Response({
            'message': f'Welcome to {invitation.tenant.name}! Your account is ready.',
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            'tenant': {
                'id': str(invitation.tenant.id),
                'name': invitation.tenant.name,
            }
        }, status=status.HTTP_201_CREATED)


class ImpersonateTenantView(APIView):
    """
    POST /api/v1/admin/impersonate/<tenant_id>/
    Super admin begins acting as a specific client tenant.

    POST /api/v1/admin/impersonate/stop/
    Stop impersonation and return to admin view.
    """
    permission_classes = [IsSuperAdmin]

    def post(self, request, tenant_id=None):
        if tenant_id == 'stop' or str(tenant_id) == 'stop':
            request.session.pop('impersonating_tenant_id', None)
            logger.info(f"Admin {request.user.email} stopped impersonation")
            return Response({'message': 'Returned to admin view.'})

        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return Response({'error': True, 'message': 'Tenant not found.'}, status=404)

        request.session['impersonating_tenant_id'] = str(tenant.id)
        logger.info(f"Admin {request.user.email} now impersonating: {tenant.name}")

        return Response({
            'message': f'You are now acting as {tenant.name}.',
            'tenant': TenantSerializer(tenant).data,
        })


class AdminOverviewView(APIView):
    """
    GET /api/v1/admin/overview/
    Cross-client summary for the admin dashboard.
    Total clients, revenue, active pipelines etc.
    """
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):
        from django.db.models import Sum, Count
        from apps.sales.models import Sale
        from apps.pipeline.models import PipelineDeal
        from datetime import date

        today = date.today()
        month_start = today.replace(day=1)

        tenants = Tenant.objects.all()
        total_tenants = tenants.count()
        active_tenants = tenants.filter(status__in=['active', 'trial']).count()

        # Cross-client revenue this month
        monthly_revenue = Sale.objects.filter(
            sale_date__gte=month_start,
            is_confirmed=True,
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Cross-client open pipeline deals
        open_deals = PipelineDeal.objects.filter(
            stage__in=['new_click', 'contacted', 'interested', 'negotiating']
        ).count()

        # Per-tenant summary
        tenant_summaries = []
        for tenant in tenants.order_by('name'):
            rev = Sale.objects.filter(
                tenant=tenant,
                sale_date__gte=month_start,
                is_confirmed=True,
            ).aggregate(total=Sum('amount'))['total'] or 0

            deals = PipelineDeal.objects.filter(
                tenant=tenant,
                stage__in=['new_click', 'contacted', 'interested', 'negotiating']
            ).count()

            last_sale = Sale.objects.filter(
                tenant=tenant
            ).order_by('-sale_date').values('sale_date').first()

            tenant_summaries.append({
                'id': str(tenant.id),
                'name': tenant.name,
                'status': tenant.status,
                'currency': tenant.currency,
                'monthly_revenue': rev,
                'open_pipeline_deals': deals,
                'last_sale_date': last_sale['sale_date'] if last_sale else None,
                'meta_fb_connected': tenant.meta_fb_connected,
                'meta_ig_connected': tenant.meta_ig_connected,
            })

        return Response({
            'summary': {
                'total_tenants': total_tenants,
                'active_tenants': active_tenants,
                'total_monthly_revenue': monthly_revenue,
                'total_open_pipeline_deals': open_deals,
            },
            'tenants': tenant_summaries,
        })


class TenantMembersView(APIView):
    """GET /api/v1/tenants/<id>/members/ — list members of a tenant"""
    permission_classes = [IsAuthenticated]

    def get(self, request, tenant_id):
        from apps.tenants.models import TenantUser
        members = TenantUser.objects.filter(tenant_id=tenant_id).select_related('user')
        from django.utils.dateformat import format as dformat
        data = []
        for m in members:
            data.append({
                'id':         str(m.id),
                'user_email': m.user.email or m.user.username,
                'role':       m.role,
                'is_active':  m.is_active,
                'joined_at':  m.joined_at.strftime('%d %b %Y') if m.joined_at else '',
            })
        return Response(data)
