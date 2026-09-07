from django.db import migrations, models
import django.db.models.deletion
import uuid
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tenants', '0001_initial'),
        ('meta_integration', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Sale',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('product_name', models.CharField(max_length=300)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=14)),
                ('payment_method', models.CharField(choices=[('mpesa_manual','M-Pesa (Manual)'),('mpesa_auto','M-Pesa (Auto)'),('cash','Cash'),('bank_deposit','Bank Deposit'),('eft','EFT'),('rtgs','RTGS'),('standing_order','Standing Order'),('cheque','Cheque'),('card','Card'),('other','Other')], default='cash', max_length=30)),
                ('payment_reference', models.CharField(blank=True, max_length=100, default='')),
                ('platform_source', models.CharField(choices=[('facebook','Facebook'),('instagram','Instagram'),('messenger','Messenger'),('organic','Organic'),('referral','Referral'),('other','Other')], default='facebook', max_length=20)),
                ('sale_date', models.DateField()),
                ('notes', models.TextField(blank=True, default='')),
                ('is_confirmed', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sales', to='tenants.tenant')),
                ('ad', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sales', to='meta_integration.ad')),
                ('campaign', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sales', to='meta_integration.campaign')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sales_created', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'sales', 'ordering': ['-sale_date', '-created_at']},
        ),
    ]
