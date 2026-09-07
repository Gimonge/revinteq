from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('tenants', '0003_add_all_missing_columns'),
    ]
    operations = [
        migrations.AlterField(
            model_name='tenant',
            name='status',
            field=models.CharField(
                choices=[('active', 'Active'), ('inactive', 'Inactive')],
                default='active',
                max_length=20,
            ),
        ),
        # Migrate existing trial/suspended to active
        migrations.RunSQL(
            "UPDATE tenants SET status = 'active' WHERE status IN ('trial', 'suspended');",
            reverse_sql="SELECT 1;"
        ),
    ]
