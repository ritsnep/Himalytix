from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
import os

# Import both default data scripts
from scripts.create_default_data import create_default_data
from scripts.create_accounting_defaults import create_defaults

class Command(BaseCommand):
    help = "Sets up all system defaults: superuser, permissions, roles, accounting, and organization data."

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(is_superuser=True).exists():
            username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
            email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin')
            self.stdout.write(f"Creating default superuser '{username}'...")
            User.objects.create_superuser(username=username, email=email, password=password)
        else:
            self.stdout.write('Superuser already exists, skipping creation.')

        self.stdout.write('Generating permissions for all models...')
        call_command('generate_permissions')
        self.stdout.write('Setting up default roles for all organizations...')
        call_command('setup_default_roles')

        self.stdout.write('Creating Nepal-specific default data...')
        create_default_data()
        self.stdout.write('Creating generic accounting defaults...')
        create_defaults()

        self.stdout.write(self.style.SUCCESS('All system defaults have been set up successfully!')) 