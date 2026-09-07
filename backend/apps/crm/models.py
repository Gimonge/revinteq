"""Revinteq CRM — Internal sales tracking for Gimsc Solutions"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class CRMUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra)


class CRMUser(AbstractBaseUser, PermissionsMixin):
    # Override to avoid clashes with auth.User
    groups = models.ManyToManyField(
        'auth.Group', blank=True,
        related_name='crm_users',
        related_query_name='crm_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission', blank=True,
        related_name='crm_users',
        related_query_name='crm_user',
    )
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email      = models.EmailField(unique=True)
    name       = models.CharField(max_length=100)
    role       = models.CharField(max_length=20, choices=[
        ("admin","Admin"),("sales","Sales Rep"),("viewer","Viewer")
    ], default="sales")
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    objects    = CRMUserManager()
    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["name"]
    class Meta:
        db_table = "crm_users"
    def __str__(self):
        return f"{self.name} <{self.email}>"


class CRMContact(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name         = models.CharField(max_length=200)
    email        = models.EmailField(blank=True)
    phone        = models.CharField(max_length=30, blank=True)
    position     = models.CharField(max_length=100, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    linkedin     = models.URLField(blank=True)
    notes        = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = "crm_contacts"
        ordering = ["name"]
    def __str__(self):
        return f"{self.name} - {self.company_name}"


class CRMLead(models.Model):
    SOURCES = [
        ("google_maps","Google Maps"),("linkedin","LinkedIn"),
        ("referral","Referral"),("cold_outreach","Cold Outreach"),
        ("inbound","Inbound"),("event","Event/Conference"),("manual","Manual Entry"),
    ]
    STATUS = [
        ("new","New"),("contacted","Contacted"),("proposal","Proposal Sent"),
        ("negotiation","Negotiation"),("won","Won"),("lost","Lost"),
    ]
    INDUSTRY = [
        ("digital_marketing","Digital Marketing Agency"),("ecommerce","E-Commerce"),
        ("fashion","Fashion & Apparel"),("real_estate","Real Estate"),
        ("education","Education"),("hospitality","Hospitality"),
        ("healthcare","Healthcare"),("finance","Finance & Insurance"),
        ("fmcg","FMCG"),("other","Other"),
    ]
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name     = models.CharField(max_length=200)
    industry         = models.CharField(max_length=50, choices=INDUSTRY, default="digital_marketing")
    source           = models.CharField(max_length=30, choices=SOURCES, default="manual")
    status           = models.CharField(max_length=20, choices=STATUS, default="new")
    website          = models.URLField(blank=True)
    instagram        = models.CharField(max_length=100, blank=True)
    facebook         = models.CharField(max_length=100, blank=True)
    location         = models.CharField(max_length=100, blank=True, default="Nairobi")
    monthly_ad_spend = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    estimated_value  = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    probability      = models.IntegerField(default=20)
    contact          = models.ForeignKey(CRMContact, on_delete=models.SET_NULL, null=True, blank=True, related_name="leads")
    assigned_to      = models.ForeignKey(CRMUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="leads")
    notes            = models.TextField(blank=True)
    lost_reason      = models.CharField(max_length=200, blank=True)
    converted_tenant_id = models.UUIDField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)
    contacted_at     = models.DateTimeField(null=True, blank=True)
    won_at           = models.DateTimeField(null=True, blank=True)
    lost_at          = models.DateTimeField(null=True, blank=True)
    class Meta:
        db_table = "crm_leads"
        ordering = ["-created_at"]
    def __str__(self):
        return f"{self.company_name} [{self.status}]"
    def save(self, *args, **kwargs):
        now = timezone.now()
        if self.status == "contacted" and not self.contacted_at:
            self.contacted_at = now
        if self.status == "won" and not self.won_at:
            self.won_at = now
        if self.status == "lost" and not self.lost_at:
            self.lost_at = now
        super().save(*args, **kwargs)


class CRMActivity(models.Model):
    TYPES = [
        ("call","Phone Call"),("email","Email"),("whatsapp","WhatsApp"),
        ("meeting","Meeting"),("demo","Product Demo"),("proposal","Proposal"),
        ("follow_up","Follow Up"),("note","Note"),
    ]
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lead         = models.ForeignKey(CRMLead, on_delete=models.CASCADE, related_name="activities")
    type         = models.CharField(max_length=20, choices=TYPES)
    subject      = models.CharField(max_length=200)
    notes        = models.TextField(blank=True)
    outcome      = models.CharField(max_length=200, blank=True)
    due_date     = models.DateTimeField(null=True, blank=True)
    completed    = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by   = models.ForeignKey(CRMUser, on_delete=models.SET_NULL, null=True, related_name="activities")
    created_at   = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "crm_activities"
        ordering = ["-created_at"]
    def __str__(self):
        return f"{self.type} - {self.lead.company_name}"


# ── CRM Customer ──────────────────────────────────────────────

class CRMCustomer(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lead         = models.OneToOneField(CRMLead, on_delete=models.SET_NULL, null=True, blank=True, related_name='customer')
    company_name = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=200, blank=True)
    email        = models.EmailField(blank=True)
    phone        = models.CharField(max_length=30, blank=True)
    address      = models.TextField(blank=True)
    website      = models.URLField(blank=True)
    notes        = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'crm_customers'
        ordering = ['company_name']

    def __str__(self):
        return self.company_name


# ── CRM Invoice ───────────────────────────────────────────────

class CRMInvoice(models.Model):
    STATUS = [
        ('draft',    'Draft'),
        ('sent',     'Sent'),
        ('paid',     'Paid'),
        ('partial',  'Partial'),
        ('overdue',  'Overdue'),
        ('cancelled','Cancelled'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_no   = models.CharField(max_length=50, unique=True)
    customer     = models.ForeignKey(CRMCustomer, on_delete=models.CASCADE, related_name='invoices')
    lead         = models.ForeignKey(CRMLead, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    status       = models.CharField(max_length=20, choices=STATUS, default='draft')
    issue_date   = models.DateField()
    due_date     = models.DateField(null=True, blank=True)
    notes        = models.TextField(blank=True)
    terms        = models.TextField(blank=True, default='Payment due within 30 days.')
    subtotal     = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_rate     = models.DecimalField(max_digits=5, decimal_places=2, default=16)
    tax_amount   = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total        = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_paid  = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'crm_invoices'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.invoice_no} — {self.customer.company_name}"

    @property
    def balance_due(self):
        return self.total - self.amount_paid

    def save(self, *args, **kwargs):
        # Auto-generate invoice number
        if not self.invoice_no:
            from django.utils import timezone
            year  = timezone.now().year
            count = CRMInvoice.objects.filter(created_at__year=year).count() + 1
            self.invoice_no = f"INV-{year}-{count:04d}"
        # Calculate totals
        items = self.items.all() if self.pk else []
        self.subtotal   = sum(i.amount for i in items)
        self.tax_amount = round(self.subtotal * self.tax_rate / 100, 2)
        self.total      = self.subtotal + self.tax_amount
        self.amount_paid = sum(r.amount for r in self.receipts.all()) if self.pk else 0
        # Update status
        if self.pk:
            if self.amount_paid >= self.total:
                self.status = 'paid'
            elif self.amount_paid > 0:
                self.status = 'partial'
        super().save(*args, **kwargs)


class CRMInvoiceItem(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice     = models.ForeignKey(CRMInvoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=300)
    quantity    = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price  = models.DecimalField(max_digits=14, decimal_places=2)
    amount      = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        db_table = 'crm_invoice_items'

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)


# ── CRM Receipt ───────────────────────────────────────────────

class CRMReceipt(models.Model):
    METHODS = [
        ('mpesa',        'M-Pesa'),
        ('bank_transfer','Bank Transfer'),
        ('cash',         'Cash'),
        ('cheque',       'Cheque'),
        ('card',         'Card'),
        ('other',        'Other'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice     = models.ForeignKey(CRMInvoice, on_delete=models.CASCADE, related_name='receipts')
    amount      = models.DecimalField(max_digits=14, decimal_places=2)
    method      = models.CharField(max_length=20, choices=METHODS, default='mpesa')
    reference   = models.CharField(max_length=100, blank=True)
    notes       = models.TextField(blank=True)
    received_at = models.DateField()
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crm_receipts'
        ordering = ['-received_at']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update invoice amount_paid and status
        invoice = self.invoice
        invoice.amount_paid = sum(r.amount for r in invoice.receipts.all())
        if invoice.amount_paid >= invoice.total:
            invoice.status = 'paid'
        elif invoice.amount_paid > 0:
            invoice.status = 'partial'
        CRMInvoice.objects.filter(pk=invoice.pk).update(
            amount_paid=invoice.amount_paid,
            status=invoice.status
        )
