"""
Management command to delete orphaned pages from deleted apps.

This command identifies and deletes pages whose content types no longer exist,
which can occur when an app is removed from the project.

This uses raw SQL to bypass Django's ORM and Wagtail's page tree management,
which fail when the model classes no longer exist.
"""
from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.contrib.contenttypes.models import ContentType
from wagtail.models import Page


class Command(BaseCommand):
    help = 'Delete orphaned pages from deleted apps'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force deletion without confirmation',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        # Find pages with missing content types
        orphaned_pages = []
        orphaned_content_types = {}

        for page in Page.objects.all().specific(defer=True):
            # Try to get the specific page type
            try:
                # If content_type.model_class() returns None, it's orphaned
                if page.content_type.model_class() is None:
                    orphaned_pages.append(page)
                    ct = page.content_type
                    if ct.id not in orphaned_content_types:
                        orphaned_content_types[ct.id] = {
                            'app_label': ct.app_label,
                            'model': ct.model,
                            'table': f'{ct.app_label}_{ct.model}',
                        }
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error checking page {page.id}: {e}')
                )

        if not orphaned_pages:
            self.stdout.write(
                self.style.SUCCESS('No orphaned pages found.')
            )
            return

        # Display orphaned pages
        self.stdout.write(
            self.style.WARNING(
                f'\nFound {len(orphaned_pages)} orphaned page(s):'
            )
        )
        for page in orphaned_pages:
            self.stdout.write(
                f'  - ID: {page.id}, '
                f'Title: "{page.title}", '
                f'Type: {page.content_type.app_label}.{page.content_type.model}'
            )

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS('\n[DRY RUN] No pages were deleted.')
            )
            return

        # Confirm deletion
        if not force:
            confirm = input('\nDelete these pages? [y/N]: ')
            if confirm.lower() != 'y':
                self.stdout.write(self.style.ERROR('Deletion cancelled.'))
                return

        # Delete using raw SQL to bypass ORM
        deleted_count = 0
        with transaction.atomic():
            cursor = connection.cursor()

            for page in orphaned_pages:
                page_id = page.id
                page_title = page.title
                ct_info = orphaned_content_types[page.content_type.id]

                try:
                    # Check if child table exists
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                        [ct_info['table']]
                    )
                    if cursor.fetchone():
                        # Delete from child table first
                        # Table names can't be parameterized, but values can
                        delete_sql = f"DELETE FROM {ct_info['table']} WHERE page_ptr_id = ?"
                        cursor.execute(delete_sql, [page_id])
                        self.stdout.write(
                            f"  Deleted from {ct_info['table']}: page_ptr_id={page_id}"
                        )

                    # Delete from wagtailcore_page using raw SQL
                    cursor.execute(
                        "DELETE FROM wagtailcore_page WHERE id = ?",
                        [page_id]
                    )
                    deleted_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Deleted page {page_id}: "{page_title}"'
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Failed to delete page {page_id}: {e}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully deleted {deleted_count} orphaned page(s).'
            )
        )

        # Clean up orphaned ContentTypes
        if orphaned_content_types:
            self.stdout.write('\nCleaning up orphaned ContentTypes...')
            for ct_id, ct_info in orphaned_content_types.items():
                try:
                    ContentType.objects.filter(id=ct_id).delete()
                    self.stdout.write(
                        f"  Deleted ContentType: {ct_info['app_label']}.{ct_info['model']}"
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Failed to delete ContentType {ct_id}: {e}"
                        )
                    )
