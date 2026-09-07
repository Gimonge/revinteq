from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0001_initial'),
        ('pipeline', '0001_initial'),
        ('bulk_upload', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='pipeline_deal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sales', to='pipeline.pipelinedeal'),
        ),
        migrations.AddField(
            model_name='sale',
            name='bulk_upload',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='saved_sales', to='bulk_upload.bulksalesupload'),
        ),
    ]
