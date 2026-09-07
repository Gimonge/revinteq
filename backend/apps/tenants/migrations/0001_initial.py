from django.db import migrations, models
import django.db.models.deletion
import uuid
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('status', models.CharField(choices=[('trial','Trial'),('active','Active'),('suspended','Suspended'),('inactive','Inactive')], default='trial', max_length=20)),
                ('contact_name', models.CharField(blank=True, max_length=200, default='')),
                ('contact_email', models.EmailField(blank=True)),
                ('contact_phone', models.CharField(blank=True, max_length=20, default='')),
                ('industry', models.CharField(blank=True, max_length=100, default='')),
                ('location', models.CharField(blank=True, max_length=200, default='')),
                ('currency', models.CharField(default='KES', max_length=10)),
                ('whatsapp_number', models.CharField(blank=True, max_length=20, default='')),
                ('whatsapp_default_message', models.TextField(blank=True, default='')),
                ('meta_fb_connected', models.BooleanField(default=False)),
                ('meta_ig_connected', models.BooleanField(default=False)),
                ('meta_fb_access_token', models.TextField(blank=True, default='')),
                ('meta_fb_token_expires_at', models.DateTimeField(blank=True, null=True)),
                ('budget_increase_cap_percent', models.PositiveIntegerField(default=20)),
                ('onboarding_complete', models.BooleanField(default=False)),
                ('onboarded_at', models.DateTimeField(null=True, blank=True)),
                ('notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_tenants', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'tenants', 'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='TenantUser',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('role', models.CharField(choices=[('SUPER_ADMIN','Super Admin'),('ADMIN','Admin'),('CLIENT','Client'),('VIEWER','Viewer')], default='CLIENT', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('invited_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invited_members', to=settings.AUTH_USER_MODEL)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='tenants.tenant')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tenant_memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'tenant_users'},
        ),
        migrations.CreateModel(
            name='TenantInvitation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('email', models.EmailField()),
                ('role', models.CharField(choices=[('SUPER_ADMIN','Super Admin'),('ADMIN','Admin'),('CLIENT','Client'),('VIEWER','Viewer')], default='CLIENT', max_length=20)),
                ('token', models.CharField(max_length=100, unique=True)),
                ('status', models.CharField(choices=[('pending','Pending'),('accepted','Accepted'),('expired','Expired'),('cancelled','Cancelled')], default='pending', max_length=20)),
                ('expires_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('accepted_at', models.DateTimeField(blank=True, null=True)),
                ('invited_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invitations_sent', to=settings.AUTH_USER_MODEL)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='tenants.tenant')),
            ],
            options={'db_table': 'tenant_invitations'},
        ),
    ]
