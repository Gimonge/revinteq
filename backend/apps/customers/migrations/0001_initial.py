from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tenants', '0001_initial'),
        ('meta_integration', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('name', models.CharField(blank=True, max_length=200, default='')),
                ('phone_number', models.CharField(blank=True, db_index=True, max_length=30, default='')),
                ('email', models.EmailField(blank=True)),
                ('instagram_handle', models.CharField(blank=True, max_length=100, default='')),
                ('facebook_profile_name', models.CharField(blank=True, max_length=200, default='')),
                ('messenger_user_id', models.CharField(blank=True, max_length=100, default='')),
                ('source_platform', models.CharField(choices=[('facebook','Facebook'),('instagram','Instagram'),('messenger','Messenger'),('organic','Organic / Walk-in'),('referral','Referral'),('other','Other')], default='facebook', max_length=20)),
                ('first_seen_date', models.DateField(auto_now_add=True)),
                ('last_contact_date', models.DateField(blank=True, null=True)),
                ('total_purchases', models.PositiveIntegerField(default=0)),
                ('total_spend', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('preferred_payment_method', models.CharField(blank=True, max_length=30, default='')),
                ('sms_opt_in', models.BooleanField(default=True)),
                ('email_opt_in', models.BooleanField(default=False)),
                ('tags', models.CharField(blank=True, max_length=500, default='')),
                ('notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='customers', to='tenants.tenant')),
                ('first_ad', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='first_touch_customers', to='meta_integration.ad')),
            ],
            options={'db_table': 'customers', 'ordering': ['-created_at']},
        ),
    ]
