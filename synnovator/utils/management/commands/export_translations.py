"""
Django management command to batch export wagtail-localize translation PO files.

Usage:
    uv run python manage.py export_translations [OPTIONS]

Examples:
    # Export all translations
    uv run python manage.py export_translations

    # Export only Chinese translations
    uv run python manage.py export_translations --locale=zh-hans

    # Export with Git auto-commit
    uv run python manage.py export_translations --git-commit

    # Dry run to preview
    uv run python manage.py export_translations --dry-run --verbose
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.text import slugify
from wagtail_localize.models import Translation


class Command(BaseCommand):
    help = 'Batch export wagtail-localize translation PO files'

    def add_arguments(self, parser):
        """Define all CLI options."""
        parser.add_argument(
            '--locale',
            type=str,
            default=None,
            help='Filter by locale code (e.g., zh-hans). Exports all locales if not specified.',
        )
        parser.add_argument(
            '--content-type',
            type=str,
            default=None,
            help='Filter by content type in format app.Model (e.g., home.HomePage)',
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='translations/exports',
            help='Base output directory (default: translations/exports)',
        )
        parser.add_argument(
            '--no-timestamp',
            action='store_true',
            help='Skip timestamp subdirectory (exports directly to locale dir)',
        )
        parser.add_argument(
            '--enabled-only',
            action='store_true',
            default=True,
            help='Export only enabled translations (default: True)',
        )
        parser.add_argument(
            '--disable-enabled-filter',
            action='store_false',
            dest='enabled_only',
            help='Export all translations including disabled ones',
        )
        parser.add_argument(
            '--min-completion',
            type=float,
            default=0.0,
            help='Minimum completion percentage (0-100, default: 0)',
        )
        parser.add_argument(
            '--git-commit',
            action='store_true',
            help='Auto-commit exported files to Git',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview without writing files',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose progress output',
        )

    def handle(self, *args, **options):
        """Main execution flow."""
        # Extract options
        locale = options['locale']
        content_type_str = options['content_type']
        output_dir = options['output_dir']
        no_timestamp = options['no_timestamp']
        enabled_only = options['enabled_only']
        min_completion = options['min_completion']
        git_commit = options['git_commit']
        dry_run = options['dry_run']
        verbose = options['verbose']

        # Validate min_completion
        if not 0 <= min_completion <= 100:
            raise CommandError('--min-completion must be between 0 and 100')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No files will be written'))

        # Get filtered translations queryset
        try:
            queryset = self.get_translations_queryset(
                locale=locale,
                content_type=content_type_str,
                enabled_only=enabled_only,
            )
        except Exception as e:
            raise CommandError(f'Failed to build queryset: {e}')

        if queryset.count() == 0:
            self.stdout.write(
                self.style.WARNING('No translations found matching filters.')
            )
            return

        if verbose:
            self.stdout.write(f'Found {queryset.count()} translations to export')

        # Determine output directory structure
        base_path = Path(output_dir)

        if locale:
            locale_dir = base_path / locale
        else:
            locale_dir = base_path / 'all'

        if not no_timestamp:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
            export_dir = locale_dir / timestamp
        else:
            export_dir = locale_dir

        if verbose:
            self.stdout.write(f'Export directory: {export_dir}')

        # Create directories if not dry run
        if not dry_run:
            try:
                export_dir.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                raise CommandError(f'Permission denied: {export_dir}')

        # Export translations
        exported_files, failed_exports = self.export_translations(
            queryset=queryset,
            export_dir=export_dir,
            min_completion=min_completion,
            dry_run=dry_run,
            verbose=verbose,
        )

        if not dry_run and len(exported_files) > 0:
            # Generate metadata JSON
            metadata = self.generate_metadata(
                exported_files=exported_files,
                locale=locale,
                filters={
                    'locale': locale,
                    'content_type': content_type_str,
                    'enabled_only': enabled_only,
                    'min_completion': min_completion,
                }
            )

            # Write metadata file
            metadata_path = export_dir / 'export-metadata.json'
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            if verbose:
                self.stdout.write(f'  Metadata written to {metadata_path}')

            # Create symlink to latest
            if not no_timestamp:
                self.create_latest_symlink(export_dir, locale_dir, verbose)

            # Git commit if requested
            if git_commit:
                self.git_commit_exports(
                    export_dir=export_dir,
                    count=len(exported_files),
                    locale=locale or 'all',
                    metadata=metadata,
                    verbose=verbose,
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully exported {len(exported_files)} translations to {export_dir}'
                )
            )
        elif dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'[DRY RUN] Would export {len(exported_files)} translations'
                )
            )

        if failed_exports:
            self.stderr.write(
                self.style.ERROR(
                    f'\n{len(failed_exports)} exports failed'
                )
            )
            if verbose:
                for failure in failed_exports:
                    self.stderr.write(f"  - Translation {failure['id']}: {failure['error']}")

    def get_translations_queryset(self, locale=None, content_type=None, enabled_only=True):
        """
        Build filtered Translation queryset.

        Args:
            locale: Language code to filter (e.g., 'zh-hans')
            content_type: Content type string in format 'app.Model'
            enabled_only: Only include enabled translations

        Returns:
            Filtered and optimized Translation queryset
        """
        queryset = Translation.objects.all()

        # Filter by locale
        if locale:
            queryset = queryset.filter(
                target_locale__language_code=locale
            )

        # Filter by content type
        if content_type:
            try:
                app_label, model = content_type.split('.')
                ct = ContentType.objects.get(
                    app_label=app_label.lower(),
                    model=model.lower()
                )
                queryset = queryset.filter(source__object__content_type=ct)
            except ValueError:
                raise CommandError(
                    f'Invalid content type format: {content_type}. '
                    'Use format: app.Model (e.g., home.HomePage)'
                )
            except ContentType.DoesNotExist:
                raise CommandError(f'Content type not found: {content_type}')

        # Filter by enabled status
        if enabled_only:
            queryset = queryset.filter(enabled=True)

        # Optimize with select_related and prefetch_related
        queryset = queryset.select_related(
            'source',
            'source__object_content_type',
            'target_locale',
        )

        return queryset

    def generate_filename(self, translation):
        """
        Generate consistent filename for a translation.

        Pattern: {app}-{model}-{identifier}-{locale}.po

        Args:
            translation: Translation instance

        Returns:
            Filename string
        """
        source = translation.source
        locale = translation.target_locale.language_code

        # Get content type info
        content_type = source.object_content_type
        app_label = content_type.app_label
        model_name = content_type.model

        # Try to get a meaningful identifier from the instance
        try:
            instance = source.get_source_instance()

            # Try slug first (most common for pages)
            if hasattr(instance, 'slug'):
                identifier = instance.slug
            # Try title, slugified
            elif hasattr(instance, 'title'):
                identifier = slugify(instance.title)[:50]
            # Try name, slugified
            elif hasattr(instance, 'name'):
                identifier = slugify(instance.name)[:50]
            # Fall back to object ID
            else:
                identifier = f'id-{source.object_id}'
        except Exception:
            # If we can't get instance, use object ID
            identifier = f'id-{source.object_id}'

        # Remove empty identifier
        if not identifier or identifier == '-':
            identifier = f'id-{source.object_id}'

        return f'{app_label}-{model_name}-{identifier}-{locale}.po'

    def export_translations(self, queryset, export_dir, min_completion, dry_run, verbose):
        """
        Export translations to PO files.

        Args:
            queryset: Filtered Translation queryset
            export_dir: Path object for output directory
            min_completion: Minimum completion percentage filter
            dry_run: If True, don't write files
            verbose: If True, output detailed progress

        Returns:
            Tuple of (exported_files list, failed_exports list)
        """
        exported_files = []
        failed_exports = []

        for translation in queryset:
            try:
                # Get progress statistics
                total_segments, translated_segments = translation.get_progress()
                completion = (translated_segments / total_segments * 100) if total_segments > 0 else 0

                # Check minimum completion threshold
                if completion < min_completion:
                    if verbose:
                        self.stdout.write(
                            f'  Skipping {translation} (completion: {completion:.1f}% < {min_completion}%)'
                        )
                    continue

                # Generate filename
                filename = self.generate_filename(translation)
                filepath = export_dir / filename

                if verbose:
                    self.stdout.write(
                        f'  Exporting {translation} -> {filename} '
                        f'({translated_segments}/{total_segments} segments, {completion:.1f}%)'
                    )

                if not dry_run:
                    # Use built-in export_po() method
                    po_content = translation.export_po()

                    # Write to file
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(str(po_content))

                # Track metadata
                file_metadata = {
                    'filename': filename,
                    'translation_id': translation.id,
                    'translation_uuid': str(translation.uuid),
                    'object_type': f'{translation.source.object_content_type.app_label}.{translation.source.object_content_type.model}',
                    'object_repr': str(translation.source.get_source_instance()) if translation.source else 'Unknown',
                    'segments_total': total_segments,
                    'segments_translated': translated_segments,
                    'completion_percentage': round(completion, 2),
                    'created_at': translation.created_at.isoformat(),
                }
                exported_files.append(file_metadata)

            except Exception as e:
                failed_exports.append({
                    'id': translation.id,
                    'error': str(e),
                })
                self.stderr.write(
                    self.style.ERROR(f'Failed to export {translation}: {e}')
                )

        return exported_files, failed_exports

    def generate_metadata(self, exported_files, locale, filters):
        """
        Generate export metadata JSON.

        Args:
            exported_files: List of file metadata dicts
            locale: Locale code or None
            filters: Dict of applied filters

        Returns:
            Metadata dict
        """
        # Calculate aggregate statistics
        total_segments = sum(f['segments_total'] for f in exported_files)
        translated_segments = sum(f['segments_translated'] for f in exported_files)
        completion = (translated_segments / total_segments * 100) if total_segments > 0 else 0

        # Get Git commit if in a repo
        git_commit = None
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                capture_output=True,
                text=True,
                check=True,
            )
            git_commit = result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        metadata = {
            'export_timestamp': timezone.now().isoformat(),
            'locale': locale or 'all',
            'source_locale': 'en',  # Default source locale
            'total_translations': len(exported_files),
            'total_segments': total_segments,
            'translated_segments': translated_segments,
            'completion_percentage': round(completion, 2),
            'filters': filters,
            'files': exported_files,
        }

        if git_commit:
            metadata['git_commit'] = git_commit

        return metadata

    def create_latest_symlink(self, export_dir, locale_dir, verbose):
        """
        Create 'latest' symlink to the most recent export.

        Args:
            export_dir: Path to the timestamped export directory
            locale_dir: Path to the locale directory (parent)
            verbose: If True, output progress
        """
        latest_link = locale_dir / 'latest'

        try:
            # Remove existing symlink if it exists
            if latest_link.exists() or latest_link.is_symlink():
                latest_link.unlink()

            # Create new symlink (relative path)
            latest_link.symlink_to(export_dir.name)

            if verbose:
                self.stdout.write(f'  Created symlink: {latest_link} -> {export_dir.name}')
        except Exception as e:
            self.stderr.write(
                self.style.WARNING(f'Failed to create latest symlink: {e}')
            )

    def git_commit_exports(self, export_dir, count, locale, metadata, verbose):
        """
        Auto-commit exported files to Git.

        Args:
            export_dir: Path to export directory
            count: Number of files exported
            locale: Locale code
            metadata: Metadata dict with completion info
            verbose: If True, output progress
        """
        try:
            completion = metadata['completion_percentage']

            # Construct commit message
            commit_msg = (
                f"chore: export {count} {locale} translations "
                f"({completion:.1f}% complete)\n\n"
                f"Exported {metadata['total_translations']} translations "
                f"with {metadata['translated_segments']}/{metadata['total_segments']} segments translated.\n\n"
                f"Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
            )

            # Git add
            subprocess.run(
                ['git', 'add', str(export_dir)],
                check=True,
                capture_output=True,
            )

            # Git commit
            subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                check=True,
                capture_output=True,
            )

            if verbose:
                self.stdout.write(
                    self.style.SUCCESS(f'  Git commit created successfully')
                )

        except subprocess.CalledProcessError as e:
            self.stderr.write(
                self.style.ERROR(f'Git commit failed: {e}')
            )
        except FileNotFoundError:
            self.stderr.write(
                self.style.ERROR('Git not found. Install git to use --git-commit')
            )
