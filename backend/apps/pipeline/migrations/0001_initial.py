from django.db import migrations, models
import django.db.models.deletion
import uuid
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tenants', '0001_initial'),
        ('meta_integration', '0001_initial'),
        ('customers', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PipelineDeal',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('platform', models.CharField(choices=[('facebook','Facebook'),('instagram','Instagram'),('messenger','Messenger'),('organic','Organic'),('manual','Manual Entry')], default='facebook', max_length=20)),
                ('source', models.CharField(choices=[('whatsapp_webhook','WhatsApp Webhook'),('messenger_webhook','Messenger Webhook'),('instagram_webhook','Instagram DM Webhook'),('meta_insights','Meta Insights Sync'),('manual','Manual Entry'),('mpesa','M-Pesa Auto-Match')], default='manual', max_length=30)),
                ('whatsapp_message_id', models.CharField(blank=True, db_index=True, max_length=100, default='')),
                ('messenger_thread_id', models.CharField(blank=True, db_index=True, max_length=100, default='')),
                ('instagram_thread_id', models.CharField(blank=True, db_index=True, max_length=100, default='')),
                ('mpesa_reference', models.CharField(blank=True, db_index=True, max_length=20, unique=True, default='')),
                ('customer_name', models.CharField(blank=True, max_length=200, default='')),
                ('customer_phone', models.CharField(blank=True, max_length=20, default='')),
                ('stage', models.CharField(choices=[('new_click','New Click'),('contacted','Contacted'),('interested','Interested'),('negotiating','Negotiating'),('won','Won'),('lost','Lost')], db_index=True, default='new_click', max_length=20)),
                ('estimated_value', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('velocity', models.CharField(choices=[('hot','Hot'),('warm','Warm'),('cold','Cold')], default='cold', max_length=10)),
                ('notes', models.TextField(blank=True, default='')),
                ('days_in_current_stage', models.PositiveIntegerField(default=0)),
                ('new_click_at', models.DateTimeField(blank=True, null=True)),
                ('contacted_at', models.DateTimeField(blank=True, null=True)),
                ('interested_at', models.DateTimeField(blank=True, null=True)),
                ('negotiating_at', models.DateTimeField(blank=True, null=True)),
                ('won_at', models.DateTimeField(blank=True, null=True)),
                ('lost_at', models.DateTimeField(blank=True, null=True)),
                ('lost_reason', models.CharField(blank=True, max_length=200, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pipeline_deals', to='tenants.tenant')),
                ('ad', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pipeline_deals', to='meta_integration.ad')),
                ('campaign', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pipeline_deals', to='meta_integration.campaign')),
                ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pipeline_deals', to='customers.customer')),
            ],
            options={'db_table': 'pipeline_deals', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='StageTransitionLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('from_stage', models.CharField(max_length=20)),
                ('to_stage', models.CharField(max_length=20)),
                ('notes', models.TextField(blank=True, default='')),
                ('source', models.CharField(blank=True, max_length=30, default='')),
                ('transitioned_at', models.DateTimeField(auto_now_add=True)),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transitions', to='pipeline.pipelinedeal')),
                ('transitioned_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stage_transitions', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'stage_transition_logs'},
        ),
    ]
