from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pipeline', '0001_initial'),
        ('kommo_integration', '0003_migration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kommomatchedlead',
            name='pipeline_deal',
            field=models.OneToOneField(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='kommo_match', to='pipeline.pipelinedeal',
            ),
        ),
        migrations.AlterField(
            model_name='kommomatchedlead',
            name='match_method',
            field=models.CharField(
                blank=True, default='', max_length=20,
                choices=[
                    ('phone', 'Phone number (WhatsApp)'),
                    ('time_window', 'Nearest in time (Messenger/Instagram)'),
                    ('none', 'No ad-click match — synced from Kommo directly'),
                ],
            ),
        ),
    ]
