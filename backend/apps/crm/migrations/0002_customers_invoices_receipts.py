from django.db import migrations, models
import django.db.models.deletion
import uuid

class Migration(migrations.Migration):
    dependencies = [
        ('crm', '0001_initial'),
    ]
    operations = [
        migrations.CreateModel(
            name='CRMCustomer',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('company_name', models.CharField(max_length=200)),
                ('contact_name', models.CharField(blank=True, max_length=200)),
                ('email', models.EmailField(blank=True)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('address', models.TextField(blank=True)),
                ('website', models.URLField(blank=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('lead', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='customer', to='crm.crmlead')),
            ],
            options={'db_table': 'crm_customers', 'ordering': ['company_name']},
        ),
        migrations.CreateModel(
            name='CRMInvoice',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('invoice_no', models.CharField(max_length=50, unique=True)),
                ('status', models.CharField(choices=[('draft','Draft'),('sent','Sent'),('paid','Paid'),('partial','Partial'),('overdue','Overdue'),('cancelled','Cancelled')], default='draft', max_length=20)),
                ('issue_date', models.DateField()),
                ('due_date', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('terms', models.TextField(blank=True, default='Payment due within 30 days.')),
                ('subtotal', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('tax_rate', models.DecimalField(decimal_places=2, default=16, max_digits=5)),
                ('tax_amount', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('amount_paid', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoices', to='crm.crmcustomer')),
                ('lead', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoices', to='crm.crmlead')),
            ],
            options={'db_table': 'crm_invoices', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='CRMInvoiceItem',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('description', models.CharField(max_length=300)),
                ('quantity', models.DecimalField(decimal_places=2, default=1, max_digits=10)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=14)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=14)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='crm.crminvoice')),
            ],
            options={'db_table': 'crm_invoice_items'},
        ),
        migrations.CreateModel(
            name='CRMReceipt',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=14)),
                ('method', models.CharField(choices=[('mpesa','M-Pesa'),('bank_transfer','Bank Transfer'),('cash','Cash'),('cheque','Cheque'),('card','Card'),('other','Other')], default='mpesa', max_length=20)),
                ('reference', models.CharField(blank=True, max_length=100)),
                ('notes', models.TextField(blank=True)),
                ('received_at', models.DateField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='crm.crminvoice')),
            ],
            options={'db_table': 'crm_receipts', 'ordering': ['-received_at']},
        ),
    ]
