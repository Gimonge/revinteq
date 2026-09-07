"""
Revinteq v3 — Customer CRM Model
Auto-created/updated when pipeline deals are created.
Powers bulk SMS campaigns, today's new contacts feed,
and customer lifetime value tracking.
"""
from django.db import models
from apps.tenants.models import Tenant
import uuid


class Customer(models.Model):
    PLATFORM_CHOICES = [
        ('facebook',  'Facebook'),
        ('instagram', 'Instagram'),
        ('messenger', 'Messenger'),
        ('organic',   'Organic / Walk-in'),
        ('referral',  'Referral'),
        ('other',     'Other'),
    ]

    id     = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name='customers'
    )

    # ── Identity ───────────────────────────────────────────────
    name = models.CharField(max_length=200, blank=True, default='')
    phone_number = models.CharField(max_length=30, blank=True, db_index=True, default='')
    email                 = models.EmailField(blank=True)
    instagram_handle = models.CharField(max_length=100, blank=True, default='')
    facebook_profile_name = models.CharField(max_length=200, blank=True, default='')
    messenger_user_id = models.CharField(max_length=100, blank=True, default='')

    # ── Source ─────────────────────────────────────────────────
    source_platform = models.CharField(
        max_length=20, choices=PLATFORM_CHOICES, default='facebook'
    )
    # First ad they clicked — best attribution
    first_ad = models.ForeignKey(
        'meta_integration.Ad', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='first_touch_customers'
    )

    # ── Dates (auto-managed) ──────────────────────────────────
    first_seen_date   = models.DateField(auto_now_add=True)
    last_contact_date = models.DateField(null=True, blank=True)

    # ── Computed stats (updated on each sale/deal) ────────────
    total_purchases         = models.PositiveIntegerField(default=0)
    total_spend             = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    preferred_payment_method = models.CharField(max_length=30, blank=True, default='')

    # ── Communication preferences ─────────────────────────────
    sms_opt_in   = models.BooleanField(default=True)
    email_opt_in = models.BooleanField(default=False)

    # ── Segmentation ──────────────────────────────────────────
    tags = models.CharField(max_length=500, blank=True,
                             help_text='Comma-separated: VIP,Wholesale,Repeat', default='')
    notes = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customers'
        ordering = ['-created_at']
        indexes  = [
            models.Index(fields=['tenant', 'first_seen_date']),
            models.Index(fields=['tenant', 'source_platform']),
            models.Index(fields=['phone_number']),
        ]

    def __str__(self):
        return f"{self.name or self.phone_number or str(self.id)[:8]} ({self.tenant.name})"

    def update_stats(self):
        """Recompute totals from linked sales. Called after each sale."""
        from apps.sales.models import Sale
        from django.db.models import Sum, Count
        sales = Sale.objects.filter(
            tenant=self.tenant,
            pipeline_deal__customer=self,
            is_confirmed=True,
        )
        agg = sales.aggregate(
            total=Sum('amount'),
            count=Count('id'),
        )
        self.total_spend    = agg['total'] or 0
        self.total_purchases= agg['count'] or 0

        # Most common payment method
        most_common = (
            sales.values('payment_method')
            .annotate(n=Count('id'))
            .order_by('-n')
            .first()
        )
        if most_common:
            self.preferred_payment_method = most_common['payment_method']

        self.save(update_fields=[
            'total_spend', 'total_purchases',
            'preferred_payment_method', 'updated_at'
        ])

    @classmethod
    def get_or_create_from_sale(cls, sale):
        """
        Find or create a Customer from a manually logged Sale.
        Only runs if the sale has customer_name or customer_phone.
        Merges into existing customer if phone matches.
        """
        from datetime import date

        if not sale.customer_name and not sale.customer_phone:
            return None

        tenant   = sale.tenant
        customer = None

        # Match by phone first
        if sale.customer_phone:
            customer = cls.objects.filter(
                tenant=tenant,
                phone_number=sale.customer_phone
            ).first()

        # Match by name if no phone match
        if not customer and sale.customer_name:
            customer = cls.objects.filter(
                tenant=tenant,
                name__iexact=sale.customer_name
            ).first()

        if customer:
            # Update stats and contact date
            customer.last_contact_date = sale.sale_date
            if sale.customer_name and not customer.name:
                customer.name = sale.customer_name
            if sale.customer_phone and not customer.phone_number:
                customer.phone_number = sale.customer_phone
            customer.total_purchases += 1
            customer.total_spend     = (customer.total_spend or 0) + sale.amount
            if sale.payment_method:
                customer.preferred_payment_method = sale.payment_method
            customer.save(update_fields=[
                'last_contact_date', 'name', 'phone_number',
                'total_purchases', 'total_spend',
                'preferred_payment_method', 'updated_at'
            ])
        else:
            customer = cls.objects.create(
                tenant            = tenant,
                name              = sale.customer_name or '',
                phone_number      = sale.customer_phone or '',
                source_platform   = sale.platform_source or 'organic',
                last_contact_date = sale.sale_date,
                total_purchases   = 1,
                total_spend       = sale.amount,
                preferred_payment_method = sale.payment_method or '',
            )

        return customer

    @classmethod
    def get_or_create_from_deal(cls, deal):
        """
        Find or create a Customer record from a pipeline deal.
        Matches by phone number first, then by platform identity.
        Called automatically when a pipeline deal is created.
        """
        from datetime import date

        tenant = deal.tenant
        customer = None

        # Match by phone number
        if deal.customer_phone:
            customer = cls.objects.filter(
                tenant=tenant,
                phone_number=deal.customer_phone
            ).first()

        # Match by Instagram thread
        if not customer and deal.instagram_thread_id:
            customer = cls.objects.filter(
                tenant=tenant,
                messenger_user_id=deal.instagram_thread_id
            ).first()

        # Match by Messenger thread
        if not customer and deal.messenger_thread_id:
            customer = cls.objects.filter(
                tenant=tenant,
                messenger_user_id=deal.messenger_thread_id
            ).first()

        if customer:
            # Update contact date
            customer.last_contact_date = date.today()
            if deal.customer_name and not customer.name:
                customer.name = deal.customer_name
            if deal.customer_phone and not customer.phone_number:
                customer.phone_number = deal.customer_phone
            customer.save(update_fields=['last_contact_date', 'name', 'phone_number', 'updated_at'])
        else:
            # Create new customer
            customer = cls.objects.create(
                tenant=tenant,
                name=deal.customer_name or '',
                phone_number=deal.customer_phone or '',
                source_platform=deal.platform,
                messenger_user_id=deal.messenger_thread_id or deal.instagram_thread_id or '',
                first_ad=deal.ad,
                last_contact_date=date.today(),
            )

        # Link deal to customer
        if not deal.customer_id:
            deal.customer = customer
            deal.save(update_fields=['customer'])

        return customer
