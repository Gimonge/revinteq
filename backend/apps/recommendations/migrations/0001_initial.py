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
            name='Recommendation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('rule_id', models.CharField(max_length=10)),
                ('title', models.CharField(max_length=300)),
                ('body', models.TextField()),
                ('priority', models.CharField(choices=[('HIGH','High'),('MEDIUM','Medium'),('LOW','Low')], default='MEDIUM', max_length=10)),
                ('platform', models.CharField(blank=True, max_length=20)),
                ('is_dismissed', models.BooleanField(default=False)),
                ('is_applied', models.BooleanField(default=False)),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recommendations', to='tenants.tenant')),
            ],
            options={'db_table': 'recommendations', 'ordering': ['-generated_at']},
        ),
    ]
