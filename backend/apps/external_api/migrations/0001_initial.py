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
            name='ExternalAPIKey',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('key', models.CharField(db_index=True, max_length=100, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('can_create_sales', models.BooleanField(default=True)),
                ('can_read_metrics', models.BooleanField(default=False)),
                ('last_used_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='api_keys', to='tenants.tenant')),
            ],
            options={'db_table': 'external_api_keys'},
        ),
        migrations.CreateModel(
            name='WebhookEndpoint',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('url', models.URLField()),
                ('secret', models.CharField(blank=True, max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('events', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='webhook_endpoints', to='tenants.tenant')),
            ],
            options={'db_table': 'webhook_endpoints'},
        ),
        migrations.CreateModel(
            name='WebhookDelivery',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('event', models.CharField(max_length=50)),
                ('payload', models.JSONField(default=dict)),
                ('status', models.CharField(choices=[('pending','Pending'),('success','Success'),('failed','Failed')], default='pending', max_length=20)),
                ('response_status_code', models.PositiveIntegerField(blank=True, null=True)),
                ('response_body', models.TextField(blank=True)),
                ('attempt_count', models.PositiveIntegerField(default=0)),
                ('delivered_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('endpoint', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deliveries', to='external_api.webhookendpoint')),
            ],
            options={'db_table': 'webhook_deliveries', 'ordering': ['-created_at']},
        ),
    ]
