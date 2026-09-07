"""
Revinteq v3 — Sales Views
Every list response includes a totals object at the bottom.
"""
from decimal import Decimal
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.common.views import get_tenant
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Avg, Q
from apps.tenants.permissions import IsClientOrAdmin, BelongsToTenant
from apps.common.pagination import StandardResultsPagination
from .models import Sale
from .serializers import SaleSerializer, SaleListSerializer


def compute_totals(queryset) -> dict:
    """
    Compute totals for any filtered Sale queryset.
    Always shown at the bottom of every sales report.
    """
    agg = queryset.aggregate(
        total_revenue=Sum('amount'),
        total_sales=Count('id'),
        avg_order_value=Avg('amount'),
        facebook_revenue=Sum('amount', filter=Q(platform_source='facebook')),
        instagram_revenue=Sum('amount', filter=Q(platform_source='instagram')),
        organic_revenue=Sum('amount', filter=Q(platform_source='organic')),
        mpesa_total=Sum('amount', filter=Q(
            payment_method__in=['mpesa_manual', 'mpesa_auto']
        )),
        cash_total=Sum('amount', filter=Q(payment_method='cash')),
        bank_total=Sum('amount', filter=Q(
            payment_method__in=['bank_deposit', 'eft', 'rtgs', 'standing_order']
        )),
    )
    # Replace None with 0 for all fields
    return {k: (v or Decimal('0')) for k, v in agg.items()}


class SaleListCreateView(APIView):
    """
    GET  /api/v1/sales/   — list sales with totals
    POST /api/v1/sales/   — log a new sale
    """
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def get(self, request):
        sales = Sale.objects.filter(
            tenant=get_tenant(request),
            is_confirmed=True,
        ).select_related('campaign', 'ad').order_by('-sale_date', '-created_at')

        # Filters
        if request.query_params.get('platform'):
            sales = sales.filter(platform_source=request.query_params['platform'])
        if request.query_params.get('payment_method'):
            sales = sales.filter(payment_method=request.query_params['payment_method'])
        if request.query_params.get('date_from'):
            sales = sales.filter(sale_date__gte=request.query_params['date_from'])
        if request.query_params.get('date_to'):
            sales = sales.filter(sale_date__lte=request.query_params['date_to'])
        if request.query_params.get('campaign'):
            sales = sales.filter(campaign_id=request.query_params['campaign'])
        if request.query_params.get('search'):
            q = request.query_params['search']
            sales = sales.filter(
                Q(product_name__icontains=q) |
                Q(payment_reference__icontains=q) |
                Q(notes__icontains=q) |
                Q(customer_name__icontains=q) |
                Q(customer_phone__icontains=q)
            )

        # Totals computed BEFORE pagination (on the full filtered set)
        totals = compute_totals(sales)

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(sales, request)
        serializer = SaleListSerializer(page, many=True)
        response = paginator.get_paginated_response(serializer.data)

        # Totals always appended
        response.data['totals'] = totals
        return response

    def post(self, request):
        serializer = SaleSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        sale = serializer.save()

        # Create/update customer record
        try:
            from apps.customers.models import Customer
            Customer.get_or_create_from_sale(sale)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Customer upsert failed: {e}")

        # Fire webhooks
        try:
            from apps.external_api.tasks import dispatch_webhook
            dispatch_webhook.delay(
                str(get_tenant(request).id), 'sale.created',
                {'sale_id': str(sale.id), 'amount': float(sale.amount),
                 'platform': sale.platform_source}
            )
        except Exception:
            pass

        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)


class SaleDetailView(APIView):
    """GET / PATCH / DELETE /api/v1/sales/<id>/"""
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def _get_sale(self, request, sale_id):
        try:
            return Sale.objects.get(id=sale_id, tenant=get_tenant(request))
        except Sale.DoesNotExist:
            return None

    def get(self, request, sale_id):
        sale = self._get_sale(request, sale_id)
        if not sale:
            return Response({'error': True, 'message': 'Sale not found.'}, status=404)
        return Response(SaleSerializer(sale).data)

    def patch(self, request, sale_id):
        sale = self._get_sale(request, sale_id)
        if not sale:
            return Response({'error': True, 'message': 'Sale not found.'}, status=404)
        serializer = SaleSerializer(
            sale, data=request.data, partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, sale_id):
        sale = self._get_sale(request, sale_id)
        if not sale:
            return Response({'error': True, 'message': 'Sale not found.'}, status=404)
        sale.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SalesSummaryView(APIView):
    """
    GET /api/v1/sales/summary/
    Totals only — used by dashboard widgets without full pagination.
    """
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def get(self, request):
        from datetime import date
        today = date.today()
        month_start = today.replace(day=1)

        sales = Sale.objects.filter(
            tenant=get_tenant(request), is_confirmed=True
        )

        period = request.query_params.get('period', 'month')
        if period == 'today':
            sales = sales.filter(sale_date=today)
        elif period == 'week':
            week_start = today - __import__('datetime').timedelta(days=today.weekday())
            sales = sales.filter(sale_date__gte=week_start)
        else:
            sales = sales.filter(sale_date__gte=month_start)

        return Response(compute_totals(sales))


class PaymentMethodChoicesView(APIView):
    """
    GET /api/v1/sales/payment-methods/
    Returns all payment methods with their reference field labels.
    Used by the frontend to dynamically show/hide reference field.
    """
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def get(self, request):
        from .serializers import REFERENCE_LABELS
        return Response({
            'payment_methods': [
                {
                    'value': value,
                    'label': label,
                    'reference_label': REFERENCE_LABELS.get(value),
                    'reference_required': value in {
                        'mpesa_manual', 'mpesa_auto', 'bank_deposit',
                        'eft', 'rtgs', 'standing_order', 'cheque', 'card',
                    }
                }
                for value, label in Sale.PAYMENT_METHOD_CHOICES
            ]
        })


class DailySalesView(APIView):
    """GET /api/v1/sales/daily/?days=7 — daily revenue for last N days"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        import datetime
        from django.utils import timezone
        from django.db.models import Sum
        from apps.common.views import get_tenant

        tenant = get_tenant(request)
        if not tenant:
            return Response([])

        days = int(request.query_params.get('days', 7))
        today = timezone.now().date()
        start = today - datetime.timedelta(days=days - 1)

        # Include sales where is_confirmed is True OR NULL (legacy rows before column existed)
        from django.db.models import Q
        sales = Sale.objects.filter(
            Q(is_confirmed=True) | Q(is_confirmed__isnull=True),
            tenant=tenant,
            sale_date__gte=start,
            sale_date__lte=today,
        ).values('sale_date').annotate(amount=Sum('amount')).order_by('sale_date')

        sales_map = {s['sale_date']: float(s['amount'] or 0) for s in sales}
        result = []
        for i in range(days):
            d = start + datetime.timedelta(days=i)
            result.append({'date': d.isoformat(), 'amount': sales_map.get(d, 0)})

        return Response(result)
