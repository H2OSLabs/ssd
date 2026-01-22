"""
Management command to seed initial notification for admin user.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from synnovator.notifications.models import Notification

User = get_user_model()


class Command(BaseCommand):
    help = 'Create initial login success notification for admin user'

    def handle(self, *args, **options):
        try:
            admin = User.objects.get(username='admin')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Admin user not found. Create one first.')
            )
            return

        # Check if login notification already exists
        existing = Notification.objects.filter(
            recipient=admin,
            notification_type='login_success'
        ).exists()

        if existing:
            self.stdout.write(
                self.style.WARNING('Login notification already exists for admin.')
            )
            return

        Notification.objects.create(
            recipient=admin,
            notification_type='login_success',
            title='Login Successful',
            message='You have successfully logged in.',
            is_read=True,
        )

        self.stdout.write(
            self.style.SUCCESS('Created login success notification for admin.')
        )
