"""
Fix NOT NULL failures by setting empty string on any NULL text columns.
Safe to run on existing databases.
"""
from django.db import migrations

FIX_NULLS = [
    "UPDATE tenants SET contact_name='' WHERE contact_name IS NULL",
    "UPDATE tenants SET contact_phone='' WHERE contact_phone IS NULL",
    "UPDATE tenants SET industry='' WHERE industry IS NULL",
    "UPDATE tenants SET location='' WHERE location IS NULL",
    "UPDATE tenants SET whatsapp_number='' WHERE whatsapp_number IS NULL",
    "UPDATE tenants SET whatsapp_default_message='' WHERE whatsapp_default_message IS NULL",
    "UPDATE tenants SET meta_fb_access_token='' WHERE meta_fb_access_token IS NULL",
    "UPDATE tenants SET notes='' WHERE notes IS NULL",
]


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(sql, reverse_sql=migrations.RunSQL.noop)
        for sql in FIX_NULLS
    ]
