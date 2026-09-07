"""Revinteq v3 — Meta Integration Serializers"""
from rest_framework import serializers
from .models import AdAccount, Campaign, Ad, AdSpendRecord


class AdAccountSerializer(serializers.ModelSerializer):
    is_token_expired       = serializers.BooleanField(read_only=True)
    days_until_token_expiry = serializers.IntegerField(read_only=True)

    class Meta:
        model  = AdAccount
        fields = [
            'id', 'meta_account_id', 'account_name', 'platform',
            'instagram_business_account_id', 'instagram_username',
            'last_synced', 'sync_enabled', 'currency',
            'is_token_expired', 'days_until_token_expiry', 'token_expires_at',
        ]
        read_only_fields = ['id', 'meta_account_id', 'last_synced']


class AdSpendRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model  = AdSpendRecord
        fields = ['id', 'date', 'spend', 'impressions', 'clicks', 'dm_conversations', 'is_partial']


class AdSerializer(serializers.ModelSerializer):
    spend_records    = AdSpendRecordSerializer(many=True, read_only=True)
    has_tracking     = serializers.SerializerMethodField()

    class Meta:
        model  = Ad
        fields = ['id', 'meta_ad_id', 'name', 'status', 'ad_format', 'has_tracking', 'spend_records']

    def get_has_tracking(self, obj):
        return True  # WhatsApp tracking via webhook — no manual link needed in v3


class CampaignListSerializer(serializers.ModelSerializer):
    max_recommended_budget = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    max_allowed_increase   = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    budget_cap_percent     = serializers.IntegerField(read_only=True)

    # Live computed metrics from AdSpendRecord
    spend         = serializers.SerializerMethodField()
    impressions   = serializers.SerializerMethodField()
    clicks        = serializers.SerializerMethodField()
    conversations = serializers.SerializerMethodField()
    ctr           = serializers.SerializerMethodField()  # Click-Through Rate %
    cpm           = serializers.SerializerMethodField()  # Cost per 1000 impressions
    cpr           = serializers.SerializerMethodField()  # Cost per DM/result
    revenue       = serializers.SerializerMethodField()
    roi           = serializers.SerializerMethodField()
    aov           = serializers.SerializerMethodField()
    last_synced   = serializers.SerializerMethodField()

    class Meta:
        model  = Campaign
        fields = [
            'id', 'meta_campaign_id', 'name', 'status', 'objective',
            'platform', 'daily_budget',
            'max_recommended_budget', 'max_allowed_increase', 'budget_cap_percent',
            'spend', 'impressions', 'clicks', 'conversations',
            'ctr', 'cpm', 'cpr', 'revenue', 'roi', 'aov', 'last_synced',
        ]

    def _records(self, obj):
        """Get this month's AdSpendRecords for this campaign, cached per serializer call."""
        if not hasattr(self, '_records_cache'):
            self._records_cache = {}
        if obj.id not in self._records_cache:
            from apps.meta_integration.models import AdSpendRecord
            from django.utils import timezone
            month_start = timezone.now().date().replace(day=1)
            self._records_cache[obj.id] = list(
                AdSpendRecord.objects.filter(
                    ad__campaign=obj,
                    date__gte=month_start,
                ).values('spend', 'impressions', 'clicks', 'dm_conversations')
            )
        return self._records_cache[obj.id]

    def get_spend(self, obj):
        return round(sum(float(r['spend'] or 0) for r in self._records(obj)), 2)

    def get_impressions(self, obj):
        return sum(int(r['impressions'] or 0) for r in self._records(obj))

    def get_clicks(self, obj):
        return sum(int(r['clicks'] or 0) for r in self._records(obj))

    def get_conversations(self, obj):
        return sum(int(r['dm_conversations'] or 0) for r in self._records(obj))

    def get_ctr(self, obj):
        impressions = self.get_impressions(obj)
        clicks      = self.get_clicks(obj)
        if impressions == 0: return 0
        return round((clicks / impressions) * 100, 2)

    def get_cpm(self, obj):
        impressions = self.get_impressions(obj)
        spend       = self.get_spend(obj)
        if impressions == 0: return 0
        return round((spend / impressions) * 1000, 2)

    def get_cpr(self, obj):
        """Cost per DM conversation — the key metric for WhatsApp-funnel businesses."""
        conversations = self.get_conversations(obj)
        spend         = self.get_spend(obj)
        if conversations == 0: return 0
        return round(spend / conversations, 2)

    def get_revenue(self, obj):
        """Revenue from sales attributed to this campaign via platform_source."""
        try:
            from apps.sales.models import Sale
            from django.utils import timezone
            from django.db.models import Sum
            month_start = timezone.now().date().replace(day=1)
            platform = obj.platform if obj.platform != 'both' else 'facebook'
            agg = Sale.objects.filter(
                tenant=obj.ad_account.tenant,
                sale_date__gte=month_start,
                platform_source=platform,
            ).aggregate(total=Sum('amount'))
            return float(agg['total'] or 0)
        except Exception:
            return 0

    def get_roi(self, obj):
        spend   = self.get_spend(obj)
        revenue = self.get_revenue(obj)
        if spend == 0: return 0
        return round(((revenue - spend) / spend) * 100, 1)

    def get_aov(self, obj):
        """Average order value for sales attributed to this campaign platform."""
        try:
            from apps.sales.models import Sale
            from django.utils import timezone
            from django.db.models import Avg
            month_start = timezone.now().date().replace(day=1)
            platform = obj.platform if obj.platform != 'both' else 'facebook'
            agg = Sale.objects.filter(
                tenant=obj.ad_account.tenant,
                sale_date__gte=month_start,
                platform_source=platform,
            ).aggregate(avg=Avg('amount'))
            return float(agg['avg'] or 0)
        except Exception:
            return 0

    def get_last_synced(self, obj):
        ls = obj.ad_account.last_synced
        if not ls: return None
        return ls.isoformat()


class CampaignDetailSerializer(CampaignListSerializer):
    ads = AdSerializer(many=True, read_only=True)

    class Meta(CampaignListSerializer.Meta):
        fields = CampaignListSerializer.Meta.fields + ['ads']
