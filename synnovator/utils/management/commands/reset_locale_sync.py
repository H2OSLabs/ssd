"""
Management command to reset wagtail-localize synchronization settings.

Use this when encountering UNIQUE constraint errors on
wagtail_localize_localesynchronization.locale_id.
"""
from django.core.management.base import BaseCommand
from wagtail_localize.models import LocaleSynchronization


class Command(BaseCommand):
    help = 'Reset wagtail-localize synchronization settings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--locale',
            type=str,
            help='Specific locale code to reset (e.g., zh-hans)',
        )

    def handle(self, *args, **options):
        locale_code = options.get('locale')

        if locale_code:
            # Reset specific locale
            syncs = LocaleSynchronization.objects.filter(
                locale__language_code=locale_code
            )
            if not syncs.exists():
                self.stdout.write(
                    self.style.WARNING(
                        f'No synchronization settings found for locale: {locale_code}'
                    )
                )
                return
        else:
            # Reset all
            syncs = LocaleSynchronization.objects.all()

        if not syncs.exists():
            self.stdout.write(
                self.style.SUCCESS('No synchronization settings to reset.')
            )
            return

        # Display what will be deleted
        self.stdout.write('Found synchronization settings:')
        for sync in syncs:
            self.stdout.write(
                f'  - Locale: {sync.locale.language_code}, '
                f'Sync from: {sync.sync_from}'
            )

        # Delete
        count = syncs.count()
        syncs.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDeleted {count} synchronization setting(s).\n'
                f'You can now reconfigure synchronization in Wagtail admin.'
            )
        )
