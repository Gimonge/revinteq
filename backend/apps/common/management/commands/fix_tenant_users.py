"""
Management command: fix_tenant_users
Ensures all TenantUser records have is_active=True.
Run if clients cannot access their portal.

Usage:
    python manage.py fix_tenant_users --settings=config.settings.local
"""
from django.core.management.base import BaseCommand
from apps.tenants.models import TenantUser


class Command(BaseCommand):
    help = 'Fix TenantUser records — ensure all are active'

    def handle(self, *args, **options):
        all_tu = TenantUser.objects.select_related('user', 'tenant').all()
        fixed = 0
        for tu in all_tu:
            self.stdout.write(
                f'  {tu.user.email or tu.user.username} → {tu.tenant.name} '
                f'[role={tu.role}, active={tu.is_active}]'
            )
            if not tu.is_active:
                tu.is_active = True
                tu.save(update_fields=['is_active'])
                fixed += 1
                self.stdout.write(self.style.SUCCESS(f'    → Fixed: set is_active=True'))

        self.stdout.write('')
        if fixed:
            self.stdout.write(self.style.SUCCESS(f'{fixed} TenantUser record(s) fixed.'))
        else:
            self.stdout.write(self.style.SUCCESS('All TenantUser records are active ✓'))
