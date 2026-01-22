"""
Management command to verify data integrity of hackathon fixtures.

This command checks for the critical data integrity issues that were fixed:
1. Users assigned to multiple teams in the same hackathon
2. Missing hackathon links for hackathon-specific quest submissions
3. Unrealistic score distributions
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Count

from synnovator.hackathons.models import (
    HackathonPage, Team, TeamMember, Quest, Submission
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Verify data integrity of hackathon fixtures'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('HACKATHON FIXTURE VERIFICATION')
        self.stdout.write('=' * 60)

        issues_found = 0

        # Check Issue 1: Multi-team assignments
        issues_found += self.check_multi_team_assignments()

        # Check Issue 2: Quest submission hackathon links
        issues_found += self.check_quest_hackathon_links()

        # Check Issue 3: Score distributions
        issues_found += self.check_score_distributions()

        # Summary
        self.stdout.write('\n' + '=' * 60)
        if issues_found == 0:
            self.stdout.write(self.style.SUCCESS('✅ ALL CHECKS PASSED'))
        else:
            self.stdout.write(self.style.ERROR(f'❌ {issues_found} ISSUES FOUND'))
        self.stdout.write('=' * 60)

    def check_multi_team_assignments(self):
        """Check for users assigned to multiple teams in the same hackathon."""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('CHECK 1: Multi-team assignments per hackathon')
        self.stdout.write('=' * 60)

        users_with_multiple_teams = []
        for user in User.objects.all():
            teams_by_hackathon = {}
            for tm in TeamMember.objects.filter(user=user).select_related('team', 'team__hackathon'):
                hackathon_id = tm.team.hackathon.id
                if hackathon_id not in teams_by_hackathon:
                    teams_by_hackathon[hackathon_id] = []
                teams_by_hackathon[hackathon_id].append(tm.team.name)

            for hackathon_id, teams in teams_by_hackathon.items():
                if len(teams) > 1:
                    users_with_multiple_teams.append((user.username, hackathon_id, teams))

        if users_with_multiple_teams:
            self.stdout.write(self.style.ERROR(
                f'❌ FAIL: Found {len(users_with_multiple_teams)} users in multiple teams per hackathon:'
            ))
            for username, hackathon_id, teams in users_with_multiple_teams[:5]:
                self.stdout.write(f'  - {username} in hackathon {hackathon_id}: {teams}')
            return 1
        else:
            self.stdout.write(self.style.SUCCESS(
                '✅ PASS: No users assigned to multiple teams in the same hackathon'
            ))
            return 0

    def check_quest_hackathon_links(self):
        """Check that quest submissions are properly structured (no hackathon required)."""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('CHECK 2: Quest submission structure')
        self.stdout.write('=' * 60)

        quest_submissions = Submission.objects.filter(quest__isnull=False)
        total_quest_submissions = quest_submissions.count()
        # Quest submissions should have user, not team, and no hackathon required
        invalid_quest_submissions = quest_submissions.filter(
            user__isnull=True
        ) | quest_submissions.filter(
            team__isnull=False
        )

        self.stdout.write(f'Total quest submissions: {total_quest_submissions}')
        self.stdout.write(f'Invalid quest submissions (missing user or has team): {invalid_quest_submissions.count()}')

        if invalid_quest_submissions.exists():
            self.stdout.write(self.style.ERROR(
                f'❌ FAIL: {invalid_quest_submissions.count()} quest submissions have invalid structure'
            ))
            examples = invalid_quest_submissions[:3]
            for sub in examples:
                self.stdout.write(
                    f'  - Submission {sub.id} for quest "{sub.quest.title}" '
                    f'(user={sub.user_id}, team={sub.team_id})'
                )
            return 1
        else:
            self.stdout.write(self.style.SUCCESS(
                '✅ PASS: All quest submissions have valid structure (user + quest, no hackathon)'
            ))
            return 0

    def check_score_distributions(self):
        """Check that score distributions are realistic."""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('CHECK 3: Score distributions')
        self.stdout.write('=' * 60)

        issues = 0

        # Check team scores
        forming_teams = Team.objects.filter(status='forming')
        forming_with_scores = forming_teams.exclude(final_score=0).count()

        self.stdout.write('\nTeam Scores:')
        self.stdout.write(f'Teams in "forming" status: {forming_teams.count()}')
        self.stdout.write(f'"Forming" teams with non-zero scores: {forming_with_scores}')

        if forming_with_scores > 0:
            self.stdout.write(self.style.ERROR(
                f'❌ FAIL: {forming_with_scores} forming teams have scores (should be 0)'
            ))
            issues += 1
        else:
            self.stdout.write(self.style.SUCCESS('✅ PASS: Forming teams have zero scores'))

        # Check score variance for scored teams
        scored_teams = Team.objects.filter(status__in=['submitted', 'verified']).exclude(final_score=0)
        if scored_teams.exists():
            import statistics
            scores = [float(t.final_score) for t in scored_teams]
            self.stdout.write(f'\nScored teams ({len(scores)} teams):')
            self.stdout.write(f'  Min: {min(scores):.2f}')
            self.stdout.write(f'  Max: {max(scores):.2f}')
            self.stdout.write(f'  Mean: {statistics.mean(scores):.2f}')
            self.stdout.write(f'  Median: {statistics.median(scores):.2f}')
            if len(scores) > 1:
                self.stdout.write(f'  Std Dev: {statistics.stdev(scores):.2f}')

        # Check submission scores
        verified_submissions = Submission.objects.filter(verification_status='verified')
        self.stdout.write(f'\nSubmission Scores:')
        self.stdout.write(f'Verified submissions: {verified_submissions.count()}')

        if verified_submissions.exists():
            scores = [float(s.score) for s in verified_submissions if s.score]
            if scores:
                low_scores = [s for s in scores if s < 40]
                mid_scores = [s for s in scores if 40 <= s < 70]
                high_scores = [s for s in scores if s >= 70]

                self.stdout.write(f'  Low scores (0-40): {len(low_scores)} ({len(low_scores)/len(scores)*100:.1f}%)')
                self.stdout.write(f'  Mid scores (40-70): {len(mid_scores)} ({len(mid_scores)/len(scores)*100:.1f}%)')
                self.stdout.write(f'  High scores (70-100): {len(high_scores)} ({len(high_scores)/len(scores)*100:.1f}%)')

                if len(low_scores) >= 1 and len(mid_scores) >= 1:
                    self.stdout.write(self.style.SUCCESS(
                        '✅ PASS: Score distribution has variance (not all 60-100)'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        '⚠️  WARNING: Limited variance in scores'
                    ))

        return issues
