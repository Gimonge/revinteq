from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdAccount',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('meta_account_id', models.CharField(db_index=True, max_length=50)),
                ('name', models.CharField(max_length=200)),
                ('platform', models.CharField(choices=[('facebook','Facebook'),('instagram','Instagram')], default='facebook', max_length=20)),
                ('currency', models.CharField(default='KES', max_length=10)),
                ('access_token', models.TextField(blank=True, default='')),
                ('token_expires_at', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('last_synced_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ad_accounts', to='tenants.tenant')),
            ],
            options={'db_table': 'ad_accounts'},
        ),
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('meta_campaign_id', models.CharField(db_index=True, max_length=50)),
                ('name', models.CharField(max_length=300)),
                ('status', models.CharField(default='ACTIVE', max_length=20)),
                ('objective', models.CharField(blank=True, max_length=50)),
                ('daily_budget', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('lifetime_budget', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('platform', models.CharField(choices=[('facebook','Facebook'),('instagram','Instagram')], default='facebook', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ad_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='campaigns', to='meta_integration.adaccount')),
            ],
            options={'db_table': 'campaigns'},
        ),
        migrations.CreateModel(
            name='Ad',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('meta_ad_id', models.CharField(db_index=True, max_length=50)),
                ('name', models.CharField(max_length=300)),
                ('status', models.CharField(default='ACTIVE', max_length=20)),
                ('format', models.CharField(blank=True, max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ads', to='meta_integration.campaign')),
            ],
            options={'db_table': 'ads'},
        ),
        migrations.CreateModel(
            name='AdSpendRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('date', models.DateField()),
                ('spend', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('views', models.PositiveIntegerField(default=0)),
                ('clicks', models.PositiveIntegerField(default=0)),
                ('conversations_started', models.PositiveIntegerField(default=0)),
                ('messaging_first_reply', models.PositiveIntegerField(default=0)),
                ('messaging_new_connections', models.PositiveIntegerField(default=0)),
                ('messaging_blocked', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='spend_records', to='meta_integration.ad')),
            ],
            options={'db_table': 'ad_spend_records'},
        ),
    ]
