from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name='CRMUser',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('is_superuser', models.BooleanField(default=False)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('role', models.CharField(choices=[('admin','Admin'),('sales','Sales Rep'),('viewer','Viewer')], default='sales', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('groups', models.ManyToManyField(blank=True, related_name='crm_users', to='auth.group')),
                ('user_permissions', models.ManyToManyField(blank=True, related_name='crm_users', to='auth.permission')),
            ],
            options={'db_table': 'crm_users'},
        ),
        migrations.CreateModel(
            name='CRMContact',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('email', models.EmailField(blank=True)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('position', models.CharField(blank=True, max_length=100)),
                ('company_name', models.CharField(blank=True, max_length=200)),
                ('linkedin', models.URLField(blank=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'crm_contacts', 'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='CRMLead',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('company_name', models.CharField(max_length=200)),
                ('industry', models.CharField(choices=[('digital_marketing','Digital Marketing Agency'),('ecommerce','E-Commerce'),('fashion','Fashion & Apparel'),('real_estate','Real Estate'),('education','Education'),('hospitality','Hospitality'),('healthcare','Healthcare'),('finance','Finance & Insurance'),('fmcg','FMCG'),('other','Other')], default='digital_marketing', max_length=50)),
                ('source', models.CharField(choices=[('google_maps','Google Maps'),('linkedin','LinkedIn'),('referral','Referral'),('cold_outreach','Cold Outreach'),('inbound','Inbound'),('event','Event/Conference'),('manual','Manual Entry')], default='manual', max_length=30)),
                ('status', models.CharField(choices=[('new','New'),('contacted','Contacted'),('proposal','Proposal Sent'),('negotiation','Negotiation'),('won','Won'),('lost','Lost')], default='new', max_length=20)),
                ('website', models.URLField(blank=True)),
                ('instagram', models.CharField(blank=True, max_length=100)),
                ('facebook', models.CharField(blank=True, max_length=100)),
                ('location', models.CharField(blank=True, default='Nairobi', max_length=100)),
                ('monthly_ad_spend', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('estimated_value', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('probability', models.IntegerField(default=20)),
                ('notes', models.TextField(blank=True)),
                ('lost_reason', models.CharField(blank=True, max_length=200)),
                ('converted_tenant_id', models.UUIDField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('contacted_at', models.DateTimeField(blank=True, null=True)),
                ('won_at', models.DateTimeField(blank=True, null=True)),
                ('lost_at', models.DateTimeField(blank=True, null=True)),
                ('contact', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='leads', to='crm.crmcontact')),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='leads', to='crm.crmuser')),
            ],
            options={'db_table': 'crm_leads', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='CRMActivity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('type', models.CharField(choices=[('call','Phone Call'),('email','Email'),('whatsapp','WhatsApp'),('meeting','Meeting'),('demo','Product Demo'),('proposal','Proposal'),('follow_up','Follow Up'),('note','Note')], max_length=20)),
                ('subject', models.CharField(max_length=200)),
                ('notes', models.TextField(blank=True)),
                ('outcome', models.CharField(blank=True, max_length=200)),
                ('due_date', models.DateTimeField(blank=True, null=True)),
                ('completed', models.BooleanField(default=False)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('lead', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities', to='crm.crmlead')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='activities', to='crm.crmuser')),
            ],
            options={'db_table': 'crm_activities', 'ordering': ['-created_at']},
        ),
    ]
