from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.utils import get_random_secret_key
import getpass


class Command(BaseCommand):
    help = 'Create a superuser with custom fields'

    def handle(self, *args, **options):
        User = get_user_model()

        username = input('Username: ')
        email = input('Email: ')

        # Generate a default company ID
        company_id = f"SU_{username.upper()}"

        password = getpass.getpass('Password: ')
        password2 = getpass.getpass('Password (again): ')

        if password != password2:
            self.stderr.write("Error: Your passwords didn't match.")
            return

        if not password:
            self.stderr.write("Error: Blank passwords aren't allowed.")
            return

        # Create the superuser
        try:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                company_id_number=company_id,
                phone_number='0000000000',  # Default phone
                company_role='manager',
                section='other'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Superuser "{username}" created successfully!')
            )
        except Exception as e:
            self.stderr.write(f"Error: {e}")
