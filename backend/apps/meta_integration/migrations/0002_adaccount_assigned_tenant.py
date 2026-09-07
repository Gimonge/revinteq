from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('meta_integration', '0001_initial'),
        ('tenants', '0004_tenant_status_active_default'),
    ]
    operations = [
        migrations.AddField(
            model_name='adaccount',
            name='assigned_tenant',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='assigned_ad_accounts',
                to='tenants.tenant',
                help_text='Tenant this ad account is attributed to for sales reporting'
            ),
        ),
    ]
