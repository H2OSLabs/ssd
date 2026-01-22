"""
Management command to migrate old Submission records to new SubmissionPage records.

Only migrates hackathon submissions (team + hackathon), not quest submissions.
Quest submissions remain in the old Submission model as they serve a different purpose.
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from synnovator.hackathons.models import (
    Submission, SubmissionPage, SubmissionIndexPage, Team, TeamMember
)
from synnovator.community.models import TeamProfilePage


class Command(BaseCommand):
    help = 'Migrate hackathon submissions from Submission to SubmissionPage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes',
        )
        parser.add_argument(
            '--delete-old',
            action='store_true',
            help='Delete old Submission records after successful migration',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        delete_old = options['delete_old']

        # Get submission index page
        submission_index = SubmissionIndexPage.objects.live().first()
        if not submission_index:
            self.stderr.write(self.style.ERROR(
                'No SubmissionIndexPage found. Please create one first.'
            ))
            return

        self.stdout.write(f'Using SubmissionIndexPage: {submission_index.title} (ID: {submission_index.id})')

        # Get hackathon submissions (not quest submissions)
        hackathon_submissions = Submission.objects.filter(
            hackathon__isnull=False,
            team__isnull=False
        ).select_related('team', 'hackathon', 'verified_by')

        total = hackathon_submissions.count()
        self.stdout.write(f'Found {total} hackathon submissions to migrate')

        if total == 0:
            self.stdout.write(self.style.SUCCESS('No submissions to migrate.'))
            return

        # Build a mapping from old Team to TeamProfilePage
        # This is approximate - we match by team name
        team_profile_map = {}
        for team in Team.objects.all():
            # Try to find a TeamProfilePage with similar name
            profile = TeamProfilePage.objects.filter(title__icontains=team.name).first()
            if profile:
                team_profile_map[team.id] = profile
            else:
                self.stdout.write(self.style.WARNING(
                    f'  No TeamProfilePage found for Team "{team.name}" (ID: {team.id})'
                ))

        migrated = 0
        skipped = 0
        errors = 0

        for submission in hackathon_submissions:
            team_profile = team_profile_map.get(submission.team_id)

            # Generate a title for the SubmissionPage
            project_title = f"{submission.team.name} - {submission.hackathon.title}"
            if submission.description:
                # Use first line of description if available
                first_line = submission.description.split('\n')[0].strip()
                if first_line and len(first_line) < 200:
                    project_title = first_line

            # Generate slug
            base_slug = slugify(project_title)[:50]
            slug = base_slug
            counter = 1
            while SubmissionPage.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            # Map verification status
            status_map = {
                'pending': 'submitted',  # Map pending to submitted
                'verified': 'verified',
                'rejected': 'rejected',
            }
            new_status = status_map.get(submission.verification_status, 'submitted')

            # Build content blocks from old submission data
            content_blocks = []
            if submission.description:
                content_blocks.append({
                    'type': 'paragraph',
                    'value': f'<p>{submission.description}</p>'
                })
            if submission.submission_url:
                content_blocks.append({
                    'type': 'github_repo',
                    'value': {
                        'url': submission.submission_url,
                        'description': 'Project repository',
                        'branch': 'main'
                    }
                })

            self.stdout.write(f'\n--- Submission ID: {submission.id} ---')
            self.stdout.write(f'  Old Team: {submission.team.name}')
            self.stdout.write(f'  Hackathon: {submission.hackathon.title}')
            self.stdout.write(f'  New Title: {project_title}')
            self.stdout.write(f'  New Slug: {slug}')
            self.stdout.write(f'  TeamProfile: {team_profile.title if team_profile else "None (will use submitter)"}')
            self.stdout.write(f'  Status: {submission.verification_status} -> {new_status}')
            self.stdout.write(f'  Score: {submission.score}')

            if dry_run:
                self.stdout.write(self.style.WARNING('  [DRY RUN] Would create SubmissionPage'))
                migrated += 1
                continue

            try:
                # Get submitter from team members if no team profile
                submitter = None
                if not team_profile:
                    team_member = TeamMember.objects.filter(team=submission.team).first()
                    if team_member:
                        submitter = team_member.user

                # Create the SubmissionPage
                submission_page = SubmissionPage(
                    title=project_title[:255],
                    slug=slug,
                    team_profile=team_profile,
                    submitter=submitter,
                    tagline=submission.description[:500] if submission.description else '',
                    content=content_blocks,
                    verification_status=new_status,
                    score=submission.score,
                    feedback=submission.feedback,
                    submitted_at=submission.submitted_at,
                    verified_at=submission.verified_at,
                    verified_by=submission.verified_by,
                )

                # Validate - ensure we have either team_profile or submitter
                if not submission_page.team_profile and not submission_page.submitter:
                    self.stdout.write(self.style.WARNING(
                        f'  [SKIPPED] No team profile or submitter available'
                    ))
                    skipped += 1
                    continue

                # Add as child of submission index
                submission_index.add_child(instance=submission_page)

                # Associate with hackathon
                submission_page.hackathons.add(submission.hackathon)

                # Publish the page
                revision = submission_page.save_revision()
                revision.publish()

                self.stdout.write(self.style.SUCCESS(
                    f'  [MIGRATED] Created SubmissionPage ID: {submission_page.id}'
                ))
                migrated += 1

                # Mark old submission if requested
                if delete_old:
                    submission.delete()
                    self.stdout.write(f'  [DELETED] Old Submission ID: {submission.id}')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  [ERROR] {str(e)}'))
                errors += 1

        # Summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(f'Migration Summary:')
        self.stdout.write(f'  Total hackathon submissions: {total}')
        self.stdout.write(f'  Migrated: {migrated}')
        self.stdout.write(f'  Skipped: {skipped}')
        self.stdout.write(f'  Errors: {errors}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] No changes were made.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nMigration completed!'))
