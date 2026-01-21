from django.core.management.base import BaseCommand
from wagtail.models import Page, Locale


class Command(BaseCommand):
    help = 'Set default locale for all existing pages'

    def handle(self, *args, **options):
        en_locale = Locale.objects.get(language_code='en')

        # Update pages without locale
        pages_updated = Page.objects.filter(locale__isnull=True).update(
            locale=en_locale
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Updated {pages_updated} pages to English locale'
            )
        )
