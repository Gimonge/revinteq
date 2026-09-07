from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tenants', '0001_initial'),
        ('pipeline', '0001_initial'),
        ('sales', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MPesaConfig',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('shortcode', models.CharField(max_length=20)),
                ('shortcode_type', models.CharField(choices=[('till','Buy Goods (Till)'),('paybill','Pay Bill')], default='till', max_length=10)),
                ('consumer_key', models.CharField(blank=True, default='', max_length=200)),
                ('consumer_secret', models.CharField(blank=True, default='', max_length=200)),
                ('passkey', models.CharField(blank=True, default='', max_length=200)),
                ('environment', models.CharField(choices=[('sandbox','Sandbox'),('production','Production')], default='sandbox', max_length=15)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tenant', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='mpesa_config', to='tenants.tenant')),
            ],
            options={'db_table': 'mpesa_configs'},
        ),
        migrations.CreateModel(
            name='MPesaTransaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('transaction_id', models.CharField(db_index=True, max_length=50, unique=True)),
                ('transaction_type', models.CharField(blank=True, max_length=30, default='')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('msisdn', models.CharField(blank=True, max_length=20, default='')),
                ('first_name', models.CharField(blank=True, max_length=100, default='')),
                ('last_name', models.CharField(blank=True, max_length=100, default='')),
                ('bill_ref_number', models.CharField(blank=True, db_index=True, max_length=50, default='')),
                ('business_short_code', models.CharField(blank=True, max_length=20, default='')),
                ('transaction_time', models.DateTimeField()),
                ('status', models.CharField(choices=[('pending','Pending'),('matched','Matched'),('unmatched','Unmatched')], default='pending', max_length=20)),
                ('match_confidence', models.CharField(blank=True, max_length=30, default='')),
                ('received_at', models.DateTimeField(auto_now_add=True)),
                ('matched_at', models.DateTimeField(blank=True, null=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mpesa_transactions', to='tenants.tenant')),
                ('matched_deal', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mpesa_transactions', to='pipeline.pipelinedeal')),
                ('matched_sale', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mpesa_transactions', to='sales.sale')),
            ],
            options={'db_table': 'mpesa_transactions', 'ordering': ['-transaction_time']},
        ),
    ]
