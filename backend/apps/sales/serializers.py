"""
Revinteq v3 — Sales Serializers
All payment methods. Reference label adapts to payment method.
"""
from rest_framework import serializers
from django.db.models import Sum, Count
from datetime import date, timedelta
from .models import Sale


# Methods that require a reference field
REFERENCE_REQUIRED_METHODS = {
    'mpesa_manual', 'mpesa_auto',
    'bank_deposit', 'eft', 'rtgs',
    'standing_order', 'cheque', 'card',
}

REFERENCE_LABELS = {
    'mpesa_manual':   'M-Pesa Transaction Code',
    'mpesa_auto':     'M-Pesa Transaction Code',
    'bank_deposit':   'Bank Reference Number',
    'eft':            'EFT Reference Number',
    'rtgs':           'RTGS Reference Number',
    'standing_order': 'Standing Order Reference',
    'cheque':         'Cheque Number',
    'card':           'Card Receipt Number',
    'cash':           None,
    'other':          'Reference Number',
}


class SaleSerializer(serializers.ModelSerializer):
    payment_method_display = serializers.CharField(
        source='get_payment_method_display', read_only=True
    )
    platform_display = serializers.CharField(
        source='get_platform_source_display', read_only=True
    )
    payment_reference_label = serializers.CharField(read_only=True)
    campaign_name = serializers.CharField(
        source='campaign.name', read_only=True, allow_null=True
    )
    ad_name = serializers.CharField(
        source='ad.name', read_only=True, allow_null=True
    )

    class Meta:
        model = Sale
        fields = [
            'id', 'customer_name', 'customer_phone', 'product_name', 'amount',
            'payment_method', 'payment_method_display',
            'payment_reference', 'payment_reference_label',
            'platform_source', 'platform_display',
            'sale_date', 'is_confirmed', 'notes',
            'campaign', 'campaign_name',
            'ad', 'ad_name',
            'pipeline_deal',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate_sale_date(self, value):
        today = date.today()
        if value > today:
            raise serializers.ValidationError('Sale date cannot be in the future.')
        if value < today - timedelta(days=90):
            raise serializers.ValidationError(
                'Sale date cannot be more than 90 days in the past.'
            )
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than zero.')
        return value

    def validate(self, data):
        # Validate that reference is provided when required
        pm = data.get('payment_method', '')
        ref = data.get('payment_reference', '')
        if pm in REFERENCE_REQUIRED_METHODS and not ref:
            label = REFERENCE_LABELS.get(pm, 'Reference')
            raise serializers.ValidationError({
                'payment_reference': f'{label} is required for {pm} payments.'
            })
        return data

    def create(self, validated_data):
        validated_data['tenant'] = self.context['request'].tenant
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class SaleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    payment_method_display = serializers.CharField(
        source='get_payment_method_display', read_only=True
    )
    platform_display = serializers.CharField(
        source='get_platform_source_display', read_only=True
    )
    campaign_name = serializers.CharField(
        source='campaign.name', read_only=True, allow_null=True
    )

    class Meta:
        model = Sale
        fields = [
            'id', 'customer_name', 'customer_phone', 'product_name', 'amount',
            'payment_method', 'payment_method_display',
            'payment_reference',
            'platform_source', 'platform_display',
            'sale_date', 'campaign_name', 'is_confirmed',
        ]


class SalesTotalsSerializer(serializers.Serializer):
    """Totals row shown at the bottom of every sales table."""
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_sales = serializers.IntegerField()
    avg_order_value = serializers.DecimalField(
        max_digits=10, decimal_places=2, allow_null=True
    )
    facebook_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    instagram_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    organic_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    mpesa_total = serializers.DecimalField(max_digits=14, decimal_places=2)
    cash_total = serializers.DecimalField(max_digits=14, decimal_places=2)
    bank_total = serializers.DecimalField(max_digits=14, decimal_places=2)
