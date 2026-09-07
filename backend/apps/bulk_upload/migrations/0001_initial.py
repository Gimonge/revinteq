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
            name='BulkSalesUpload',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('original_filename', models.CharField(max_length=255)),
                ('file', models.FileField(blank=True, upload_to='bulk_uploads/')),
                ('status', models.CharField(choices=[('pending','Pending'),('previewed','Previewed'),('processing','Processing'),('completed','Completed'),('failed','Failed')], default='pending', max_length=20)),
                ('total_rows', models.PositiveIntegerField(default=0)),
                ('valid_rows', models.PositiveIntegerField(default=0)),
                ('error_rows', models.PositiveIntegerField(default=0)),
                ('saved_rows', models.PositiveIntegerField(default=0)),
                ('preview_data', models.JSONField(default=list)),
                ('error_summary', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bulk_uploads', to='tenants.tenant')),
                ('uploaded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bulk_uploads', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'bulk_sales_uploads', 'ordering': ['-created_at']},
        ),
    ]
