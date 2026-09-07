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
            name='MetricSnapshot',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('period_type', models.CharField(choices=[('day','Day'),('week','Week'),('month','Month')], default='month', max_length=10)),
                ('period_start', models.DateField()),
                ('period_end', models.DateField()),
                ('total_revenue', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('facebook_revenue', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('instagram_revenue', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('total_spend', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('roi', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('avg_order_value', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('facebook_aov', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('instagram_aov', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_sales_count', models.PositiveIntegerField(default=0)),
                ('total_conversations', models.PositiveIntegerField(default=0)),
                ('facebook_conversations', models.PositiveIntegerField(default=0)),
                ('instagram_conversations', models.PositiveIntegerField(default=0)),
                ('whatsapp_conversations', models.PositiveIntegerField(default=0)),
                ('conversion_rate', models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ('cost_per_conversation', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('cost_per_sale', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('revenue_goal', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ('goal_progress_percent', models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ('goal_status', models.CharField(blank=True, max_length=20)),
                ('revenue_gap', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('required_daily_revenue', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('computed_at', models.DateTimeField(auto_now_add=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='metric_snapshots', to='tenants.tenant')),
            ],
            options={'db_table': 'metric_snapshots', 'ordering': ['-period_start']},
        ),
    ]
