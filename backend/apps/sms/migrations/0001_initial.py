from django.db import migrations, models
import django.db.models.deletion
import uuid
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tenants', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SMSConfig',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('username', models.CharField(max_length=100)),
                ('api_key', models.CharField(blank=True, default='', max_length=200)),
                ('sender_id', models.CharField(blank=True, max_length=20, default='')),
                ('is_active', models.BooleanField(default=True)),
                ('credit_balance', models.DecimalField(decimal_places=4, default=0, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tenant', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='sms_config', to='tenants.tenant')),
            ],
            options={'db_table': 'sms_configs'},
        ),
        migrations.CreateModel(
            name='SMSMessage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('recipient_number', models.CharField(max_length=20)),
                ('recipient_name', models.CharField(blank=True, max_length=200, default='')),
                ('message', models.TextField()),
                ('source', models.CharField(choices=[('manual','Manual'),('bulk','Bulk'),('auto','Automatic Trigger')], default='manual', max_length=20)),
                ('trigger', models.CharField(blank=True, max_length=50, default='')),
                ('status', models.CharField(choices=[('queued','Queued'),('sent','Sent'),('delivered','Delivered'),('failed','Failed')], default='queued', max_length=20)),
                ('at_message_id', models.CharField(blank=True, max_length=100, default='')),
                ('at_status_code', models.CharField(blank=True, max_length=10, default='')),
                ('cost', models.FloatField(default=0.0)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sms_messages', to='tenants.tenant')),
                ('sent_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sms_sent', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'sms_messages', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='SMSTrigger',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('trigger', models.CharField(max_length=50)),
                ('message_template', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sms_triggers', to='tenants.tenant')),
            ],
            options={'db_table': 'sms_triggers'},
        ),
    ]
