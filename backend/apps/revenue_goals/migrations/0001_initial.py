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
            name='RevenueGoal',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('month', models.DateField()),
                ('target_amount', models.DecimalField(decimal_places=2, max_digits=14)),
                ('primary_channel', models.CharField(blank=True, default='whatsapp', max_length=30)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='revenue_goals', to='tenants.tenant')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='goals_created', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'revenue_goals'},
        ),
    ]
