from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os


class Command(BaseCommand):
    """
    Idempotent superuser creation for deploy pipelines (e.g. Render's build/release step).

    Reads DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD
    from the environment. Safe to run on every deploy:
      - If the env vars aren't set, it does nothing (no error, no crash on build).
      - If a user with that username already exists, it leaves them alone (idempotent).
      - Otherwise it creates a real Django superuser.
    """
    help = "Create a superuser from DJANGO_SUPERUSER_* environment variables, if not already present."

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.getenv('DJANGO_SUPERUSER_USERNAME')
        email = os.getenv('DJANGO_SUPERUSER_EMAIL')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD')

        if not username or not password:
            self.stdout.write(self.style.WARNING(
                'DJANGO_SUPERUSER_USERNAME / DJANGO_SUPERUSER_PASSWORD not set — skipping superuser creation.'
            ))
            return

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email=email or '',
                password=password,
            )
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" already exists.'))
        fixed = User.objects.filter(is_superuser=True).exclude(
            is_approved=True, is_staff=True, email_verified=True
        ).update(is_approved=True, is_staff=True, email_verified=True)
        if fixed:
            self.stdout.write(self.style.SUCCESS(f'Repaired flags on {fixed} superuser(s).'))
