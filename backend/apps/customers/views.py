"""Revinteq v3 — Customer CRM Views"""
from datetime import date
from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.common.views import get_tenant
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from apps.tenants.permissions import IsClientOrAdmin
from apps.common.pagination import StandardResultsPagination
from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    source_platform_display = serializers.CharField(
        source='get_source_platform_display', read_only=True
    )

    class Meta:
        model  = Customer
        fields = [
            'id', 'name', 'phone_number', 'email',
            'instagram_handle', 'facebook_profile_name',
            'source_platform', 'source_platform_display',
            'first_seen_date', 'last_contact_date',
            'total_purchases', 'total_spend',
            'preferred_payment_method',
            'sms_opt_in', 'email_opt_in',
            'tags', 'notes', 'created_at',
        ]
        read_only_fields = [
            'id', 'first_seen_date', 'total_purchases',
            'total_spend', 'preferred_payment_method', 'created_at',
        ]


class CustomerListView(APIView):
    """GET /api/v1/customers/"""
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def get(self, request):
        qs = Customer.objects.filter(tenant=get_tenant(request))

        # Filters
        q = request.query_params.get('search', '')
        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(phone_number__icontains=q) |
                Q(email__icontains=q) |
                Q(instagram_handle__icontains=q)
            )

        platform = request.query_params.get('platform', '')
        if platform:
            qs = qs.filter(source_platform=platform)

        opt_in = request.query_params.get('opt_in', '')
        if opt_in == 'sms':
            qs = qs.filter(sms_opt_in=True)
        elif opt_in == 'email':
            qs = qs.filter(email_opt_in=True)

        # Spend threshold for campaign targeting
        min_spend = request.query_params.get('min_spend', '')
        if min_spend:
            qs = qs.filter(total_spend__gte=min_spend)

        # Tags filter
        tag = request.query_params.get('tag', '')
        if tag:
            qs = qs.filter(tags__icontains=tag)

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(qs.order_by('-created_at'), request)
        return paginator.get_paginated_response(
            CustomerSerializer(page, many=True).data
        )

    def post(self, request):
        s = CustomerSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        customer = s.save(tenant=get_tenant(request))
        return Response(CustomerSerializer(customer).data, status=201)


class CustomerDetailView(APIView):
    """GET / PATCH /api/v1/customers/<id>/"""
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def _get(self, request, customer_id):
        try:
            return Customer.objects.get(id=customer_id, tenant=get_tenant(request))
        except Customer.DoesNotExist:
            return None

    def get(self, request, customer_id):
        c = self._get(request, customer_id)
        if not c:
            return Response({'error': True, 'message': 'Customer not found.'}, status=404)
        data = CustomerSerializer(c).data
        # Add pipeline deal history
        data['pipeline_deals'] = list(
            c.pipeline_deals.values(
                'id', 'stage', 'platform', 'created_at',
                'mpesa_reference', 'estimated_value'
            ).order_by('-created_at')[:10]
        )
        return Response(data)

    def delete(self, request, customer_id):
        c = self._get(request, customer_id)
        if not c: return Response({'error': 'Not found.'}, status=404)
        c.delete()
        return Response(status=204)

    def patch(self, request, customer_id):
        c = self._get(request, customer_id)
        if not c:
            return Response({'error': True, 'message': 'Customer not found.'}, status=404)
        s = CustomerSerializer(c, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)


class TodaysNewContactsView(APIView):
    """GET /api/v1/customers/todays-new/"""
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def get(self, request):
        today     = date.today()
        customers = Customer.objects.filter(
            tenant=get_tenant(request),
            first_seen_date=today,
        ).order_by('-created_at')[:20]
        return Response(CustomerSerializer(customers, many=True).data)


class BulkSMSListView(APIView):
    """
    GET /api/v1/customers/bulk-sms-list/
    Returns customers matching filter criteria who have SMS opt-in.
    Used to preview recipients before sending bulk campaign.
    """
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def get(self, request):
        qs = Customer.objects.filter(
            tenant=get_tenant(request),
            sms_opt_in=True,
        )
        platform  = request.query_params.get('platform', '')
        min_spend = request.query_params.get('min_spend', '')
        tag       = request.query_params.get('tag', '')

        if platform:   qs = qs.filter(source_platform=platform)
        if min_spend:  qs = qs.filter(total_spend__gte=min_spend)
        if tag:        qs = qs.filter(tags__icontains=tag)

        return Response({
            'count': qs.count(),
            'customers': CustomerSerializer(qs[:100], many=True).data,
        })
