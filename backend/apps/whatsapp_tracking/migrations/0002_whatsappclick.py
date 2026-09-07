from django.db import migrations, models
import django.db.models.deletion
import uuid

class Migration(migrations.Migration):
    dependencies = [
        ('whatsapp_tracking', '0001_initial'),
        ('tenants', '0004_tenant_status_active_default'),
        ('meta_integration', '0002_adaccount_assigned_tenant'),
    ]
    operations = [
        migrations.CreateModel(
            name='WhatsAppClick',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('platform', models.CharField(default='whatsapp', max_length=20)),
                ('message_id', models.CharField(blank=True, db_index=True, max_length=100)),
                ('sender_phone', models.CharField(blank=True, max_length=30)),
                ('meta_ad_id', models.CharField(blank=True, max_length=100)),
                ('clicked_at', models.DateTimeField(auto_now_add=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='whatsapp_clicks', to='tenants.tenant')),
                ('ad', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='meta_integration.ad')),
                ('campaign', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='meta_integration.campaign')),
            ],
            options={'db_table': 'whatsapp_clicks', 'ordering': ['-clicked_at']},
        ),
        migrations.AddIndex(
            model_name='whatsappclick',
            index=models.Index(fields=['tenant', 'clicked_at'], name='wa_tenant_date_idx'),
        ),
        migrations.AddIndex(
            model_name='whatsappclick',
            index=models.Index(fields=['campaign', 'clicked_at'], name='wa_campaign_date_idx'),
        ),
    ]
