"""
Management command: fix_superuser
Ensures the superuser has email = username so login always works.
Run once after createsuperuser if you used an email as the username.

Usage:
    python manage.py fix_superuser --settings=config.settings.local
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Fix superuser email field so login works with email address'

    def handle(self, *args, **options):
        superusers = User.objects.filter(is_superuser=True)
        fixed = 0
        for user in superusers:
            changed = False
            # If email is blank but username looks like an email, copy it
            if not user.email and '@' in user.username:
                user.email = user.username
                changed = True
            # If username is blank, set it to email
            if not user.username and user.email:
                user.username = user.email
                changed = True
            if changed:
                user.save()
                fixed += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  Fixed: {user.username} — email set to {user.email}')
                )
            else:
                self.stdout.write(f'  OK: {user.username} (email: {user.email or "already set"})')

        if fixed == 0:
            self.stdout.write(self.style.SUCCESS('All superusers are already correctly configured.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n{fixed} superuser(s) fixed. You can now log in with your email.'))
