"""
Tests for submission validation flow according to the plan:

Validation Flow (from docs/plans/2025-01-22-submission-architecture-redesign.md):

User clicks "Submit Project" on HackathonPage
    │
    ▼
HackathonPage.can_submit(user, team)
    │
    ├── Check submission_type config
    │   └── Reject if type mismatch
    │
    ├── Check require_registration config
    │   └── Reject if not registered
    │
    ├── Check max_submissions_per_participant config
    │   └── Reject if limit reached
    │
    ├── Check restrict_to_submission_phase config
    │   ├── If closed and allow_late_submission: Allow (marked late)
    │   └── If closed and not allow_late: Reject
    │
    └── Allow submission
"""

import pytest
from django.utils import timezone
from datetime import timedelta

from synnovator.hackathons.models import HackathonPage, TeamRegistration, SubmissionIndexPage, SubmissionPage
from synnovator.hackathons.tests.factories import (
    HackathonPageFactory,
    HackathonIndexPageFactory,
    ActivePhaseFactory,
    FuturePhaseFactory,
    PastPhaseFactory,
)
from synnovator.community.tests.factories import TeamProfilePageFactory, TeamMembershipFactory
from synnovator.users.tests.factories import UserFactory
from wagtail.models import Page


@pytest.fixture
def wagtail_root(db):
    """Get or create Wagtail root page."""
    root = Page.objects.filter(depth=1).first()
    if not root:
        root = Page.add_root(title="Root", slug="root")
    return root


@pytest.fixture
def submission_index(wagtail_root):
    """Create SubmissionIndexPage for tests."""
    index = SubmissionIndexPage(
        title="Submissions",
        slug="submissions",
    )
    wagtail_root.add_child(instance=index)
    return index


# =============================================================================
# Test: Submission Type Check
# =============================================================================


class TestSubmissionTypeValidation:
    """Tests for submission_type configuration validation."""

    def test_individual_only_rejects_team_submission(self, db, wagtail_root):
        """When submission_type='individual', team submissions are rejected."""
        hackathon = HackathonPageFactory(submission_type='individual')
        team = TeamProfilePageFactory()

        can_submit, reason = hackathon.can_submit(team_profile=team)

        assert can_submit is False
        assert "individual" in reason.lower() or "team" in reason.lower()

    def test_individual_only_allows_individual_submission(self, db, wagtail_root):
        """When submission_type='individual', individual submissions are allowed."""
        hackathon = HackathonPageFactory(
            submission_type='individual',
            require_registration=False,
            restrict_to_submission_phase=False,
        )
        user = UserFactory()

        can_submit, reason = hackathon.can_submit(user=user)

        assert can_submit is True

    def test_team_only_rejects_individual_submission(self, db, wagtail_root):
        """When submission_type='team', individual submissions are rejected."""
        hackathon = HackathonPageFactory(submission_type='team')
        user = UserFactory()

        can_submit, reason = hackathon.can_submit(user=user)

        assert can_submit is False
        assert "team" in reason.lower()

    def test_team_only_allows_team_submission(self, db, wagtail_root):
        """When submission_type='team', team submissions are allowed."""
        hackathon = HackathonPageFactory(
            submission_type='team',
            require_registration=False,
            restrict_to_submission_phase=False,
        )
        team = TeamProfilePageFactory()

        can_submit, reason = hackathon.can_submit(team_profile=team)

        assert can_submit is True

    def test_both_allows_individual_submission(self, db, wagtail_root):
        """When submission_type='both', individual submissions are allowed."""
        hackathon = HackathonPageFactory(
            submission_type='both',
            require_registration=False,
            restrict_to_submission_phase=False,
        )
        user = UserFactory()

        can_submit, reason = hackathon.can_submit(user=user)

        assert can_submit is True

    def test_both_allows_team_submission(self, db, wagtail_root):
        """When submission_type='both', team submissions are allowed."""
        hackathon = HackathonPageFactory(
            submission_type='both',
            require_registration=False,
            restrict_to_submission_phase=False,
        )
        team = TeamProfilePageFactory()

        can_submit, reason = hackathon.can_submit(team_profile=team)

        assert can_submit is True


# =============================================================================
# Test: Registration Requirement Check
# =============================================================================


class TestRegistrationRequirementValidation:
    """Tests for require_registration configuration validation."""

    def test_registration_required_rejects_unregistered_team(self, db, wagtail_root):
        """When require_registration=True, unregistered teams are rejected."""
        hackathon = HackathonPageFactory(
            submission_type='both',
            require_registration=True,
            restrict_to_submission_phase=False,
        )
        team = TeamProfilePageFactory()

        can_submit, reason = hackathon.can_submit(team_profile=team)

        assert can_submit is False
        assert "register" in reason.lower()

    def test_registration_required_allows_registered_team(self, db, wagtail_root):
        """When require_registration=True, registered teams are allowed."""
        hackathon = HackathonPageFactory(
            submission_type='both',
            require_registration=True,
            restrict_to_submission_phase=False,
        )
        team = TeamProfilePageFactory()

        # Register the team
        TeamRegistration.objects.create(
            hackathon=hackathon,
            team_profile=team,
            status='approved',
        )

        can_submit, reason = hackathon.can_submit(team_profile=team)

        assert can_submit is True

    def test_registration_required_pending_team_rejected(self, db, wagtail_root):
        """When require_registration=True, pending registration teams are rejected."""
        hackathon = HackathonPageFactory(
            submission_type='both',
            require_registration=True,
            restrict_to_submission_phase=False,
        )
        team = TeamProfilePageFactory()

        # Register with pending status
        TeamRegistration.objects.create(
            hackathon=hackathon,
            team_profile=team,
            status='pending',  # Not approved
        )

        can_submit, reason = hackathon.can_submit(team_profile=team)

        assert can_submit is False
        assert "register" in reason.lower()

    def test_registration_not_required_allows_unregistered(self, db, wagtail_root):
        """When require_registration=False, unregistered teams are allowed."""
        hackathon = HackathonPageFactory(
            submission_type='both',
            require_registration=False,
            restrict_to_submission_phase=False,
        )
        team = TeamProfilePageFactory()

        can_submit, reason = hackathon.can_submit(team_profile=team)

        assert can_submit is True

    def test_registration_required_checks_user_team_membership(self, db, wagtail_root):
        """When require_registration=True, checks if user is in a registered team."""
        hackathon = HackathonPageFactory(
            submission_type='both',
            require_registration=True,
            restrict_to_submission_phase=False,
        )
        user = UserFactory()
        team = TeamProfilePageFactory()

        # Add user to team
        TeamMembershipFactory(team=team, user=user)

        # Register the team
        TeamRegistration.objects.create(
            hackathon=hackathon,
            team_profile=team,
            status='approved',
        )

        can_submit, reason = hackathon.can_submit(user=user)

        assert can_submit is True


# =============================================================================
# Test: Max Submissions Check
# =============================================================================


class TestMaxSubmissionsValidation:
    """Tests for max_submissions_per_participant configuration validation."""

    def test_max_submissions_zero_allows_unlimited(self, db, wagtail_root, submission_index):
        """When max_submissions_per_participant=0, unlimited submissions allowed."""
        hackathon = HackathonPageFactory(
            submission_type='both',
            require_registration=False,
            restrict_to_submission_phase=False,
            max_submissions_per_participant=0,  # Unlimited
        )
        team = TeamProfilePageFactory()

        # Create multiple submissions
        for i in range(5):
            submission = SubmissionPage(
                title=f"Submission {i}",
                slug=f"submission-{i}-{team.pk}",
                team_profile=team,
            )
            submission_index.add_child(instance=submission)
            submission.hackathons.add(hackathon)

        can_submit, reason = hackathon.can_submit(team_profile=team)

        assert can_submit is True

    def test_max_submissions_enforced(self, db, wagtail_root, submission_index):
        """When max_submissions_per_participant > 0, limit is enforced."""
        hackathon = HackathonPageFactory(
            submission_type='both',
            require_registration=False,
            restrict_to_submission_phase=False,
            max_submissions_per_participant=2,
        )
        team = TeamProfilePageFactory()

        # Create submissions up to the limit
        for i in range(2):
            submission = SubmissionPage(
                title=f"Submission {i}",
                slug=f"submission-max-{i}-{team.pk}",
                team_profile=team,
            )
            submission_index.add_child(instance=submission)
            submission.hackathons.add(hackathon)

        can_submit, reason = hackathon.can_submit(team_profile=team)

        assert can_submit is False
        assert "maximum" in reason.lower() or "reached" in reason.lower()

    def test_max_submissions_allows_under_limit(self, db, wagtail_root, submission_index):
        """When under max_submissions_per_participant, submission is allowed."""
        hackathon = HackathonPageFactory(
            submission_type='both',
            require_registration=False,
            restrict_to_submission_phase=False,
            max_submissions_per_participant=3,
        )
        team = TeamProfilePageFactory()

        # Create only 1 submission (under limit of 3)
        submission = SubmissionPage(
            title="Submission 1",
            slug=f"submission-under-{team.pk}",
            team_profile=team,
        )
        submission_index.add_child(instance=submission)
        submission.hackathons.add(hackathon)

        can_submit, reason = hackathon.can_submit(team_profile=team)

        assert can_submit is True

    def test_max_submissions_per_user(self, db, wagtail_root, submission_index):
        """Max submissions check works for individual users."""
        hackathon = HackathonPageFactory(
            submission_type='individual',
            require_registration=False,
            restrict_to_submission_phase=False,
            max_submissions_per_participant=1,
        )
        user = UserFactory()

        # Create one submission
        submission = SubmissionPage(
            title="User Submission",
            slug=f"submission-user-{user.pk}",
            submitter=user,
        )
        submission_index.add_child(instance=submission)
        submission.hackathons.add(hackathon)

        can_submit, reason = hackathon.can_submit(user=user)

        assert can_submit is False


# =============================================================================
# Test: Phase Restriction Check
# =============================================================================


class TestPhaseRestrictionValidation:
    """Tests for restrict_to_submission_phase configuration validation."""

    def test_phase_restriction_rejects_outside_submission_phase(self, db, wagtail_root):
        """When restrict_to_submission_phase=True and not in submission phase, rejected."""
        hackathon = HackathonPageFactory(
            submission_type='both',
            require_registration=False,
            restrict_to_submission_phase=True,
            allow_late_submission=False,
            status='judging',  # Not in_progress
        )
        # Create a past submission phase and active judging phase
        PastPhaseFactory(hackathon=hackathon, title="Submission Phase (ended)")
        ActivePhaseFactory(hackathon=hackathon, title="Judging Phase")

        team = TeamProfilePageFactory()

        can_submit, reason = hackathon.can_submit(team_profile=team)

        assert can_submit is False
        assert "closed" in reason.lower()

    def test_phase_restriction_allows_during_submission_phase(self, db, wagtail_root):
        """When restrict_to_submission_phase=True and in submission phase, allowed."""
        hackathon = HackathonPageFactory(
            submission_type='both',
            require_registration=False,
            restrict_to_submission_phase=True,
            status='in_progress',
        )
        # Create an active submission phase
        ActivePhaseFactory(hackathon=hackathon, title="Submission Phase")

        team = TeamProfilePageFactory()

        can_submit, reason = hackathon.can_submit(team_profile=team)

        assert can_submit is True

    def test_late_submission_allowed_when_configured(self, db, wagtail_root):
        """When allow_late_submission=True and phase is closed, late submission allowed."""
        hackathon = HackathonPageFactory(
            submission_type='both',
            require_registration=False,
            restrict_to_submission_phase=True,
            allow_late_submission=True,
            status='judging',  # Not in_progress (submission closed)
        )
        # Create a past submission phase and current judging phase
        PastPhaseFactory(hackathon=hackathon, title="Submission Phase (ended)")
        ActivePhaseFactory(hackathon=hackathon, title="Judging Phase")

        team = TeamProfilePageFactory()

        can_submit, reason = hackathon.can_submit(team_profile=team)

        assert can_submit is True
        assert "late" in reason.lower()

    def test_no_phase_restriction_allows_anytime(self, db, wagtail_root):
        """When restrict_to_submission_phase=False, submission allowed anytime."""
        hackathon = HackathonPageFactory(
            submission_type='both',
            require_registration=False,
            restrict_to_submission_phase=False,
        )
        # No phases defined
        team = TeamProfilePageFactory()

        can_submit, reason = hackathon.can_submit(team_profile=team)

        assert can_submit is True

    def test_in_progress_status_allows_submission_when_no_phases(self, db, wagtail_root):
        """When status='in_progress' and no phases, submission allowed."""
        hackathon = HackathonPageFactory(
            submission_type='both',
            require_registration=False,
            restrict_to_submission_phase=True,
            status='in_progress',
        )
        # No phases defined - should fall back to status check
        team = TeamProfilePageFactory()

        can_submit, reason = hackathon.can_submit(team_profile=team)

        assert can_submit is True


# =============================================================================
# Test: Combined Validation Flow
# =============================================================================


class TestCombinedValidationFlow:
    """Tests for complete validation flow with multiple checks."""

    def test_full_validation_flow_success(self, db, wagtail_root):
        """Complete validation passes when all requirements are met."""
        hackathon = HackathonPageFactory(
            submission_type='team',
            require_registration=True,
            restrict_to_submission_phase=True,
            max_submissions_per_participant=5,
            status='in_progress',
        )
        ActivePhaseFactory(hackathon=hackathon, title="Hacking Phase")

        team = TeamProfilePageFactory()
        TeamRegistration.objects.create(
            hackathon=hackathon,
            team_profile=team,
            status='approved',
        )

        can_submit, reason = hackathon.can_submit(team_profile=team)

        assert can_submit is True
        assert reason == ""

    def test_validation_stops_at_first_failure(self, db, wagtail_root):
        """Validation returns first failure reason encountered."""
        hackathon = HackathonPageFactory(
            submission_type='team',  # Will fail for individual
            require_registration=True,  # Would also fail
            restrict_to_submission_phase=True,  # Would also fail
        )
        user = UserFactory()

        can_submit, reason = hackathon.can_submit(user=user)

        assert can_submit is False
        # First check is submission_type
        assert "team" in reason.lower()


# =============================================================================
# Test: SubmissionPage Model Validation
# =============================================================================


class TestSubmissionPageValidation:
    """Tests for SubmissionPage model validation."""

    def test_submission_requires_team_or_submitter(self, db, wagtail_root, submission_index):
        """SubmissionPage requires either team_profile or submitter."""
        from django.core.exceptions import ValidationError

        submission = SubmissionPage(
            title="Invalid Submission",
            slug="invalid-submission",
            team_profile=None,
            submitter=None,
        )

        with pytest.raises(ValidationError) as exc_info:
            submission.clean()

        assert "team" in str(exc_info.value).lower() or "submitter" in str(exc_info.value).lower()

    def test_submission_cannot_have_both_team_and_submitter(self, db, wagtail_root, submission_index):
        """SubmissionPage cannot have both team_profile and submitter."""
        from django.core.exceptions import ValidationError

        team = TeamProfilePageFactory()
        user = UserFactory()

        submission = SubmissionPage(
            title="Invalid Submission",
            slug="invalid-both",
            team_profile=team,
            submitter=user,
        )

        with pytest.raises(ValidationError) as exc_info:
            submission.clean()

        assert "both" in str(exc_info.value).lower()

    def test_submission_with_team_is_valid(self, db, wagtail_root, submission_index):
        """SubmissionPage with team_profile is valid."""
        team = TeamProfilePageFactory()

        submission = SubmissionPage(
            title="Team Submission",
            slug="team-submission",
            team_profile=team,
        )
        submission.clean()  # Should not raise

    def test_submission_with_submitter_is_valid(self, db, wagtail_root, submission_index):
        """SubmissionPage with submitter is valid."""
        user = UserFactory()

        submission = SubmissionPage(
            title="Individual Submission",
            slug="individual-submission",
            submitter=user,
        )
        submission.clean()  # Should not raise


# =============================================================================
# Test: SubmissionIndexPage Filters
# =============================================================================


class TestSubmissionIndexPageFilters:
    """Tests for SubmissionIndexPage filter functionality."""

    def test_filter_by_hackathon(self, db, wagtail_root, submission_index, rf):
        """SubmissionIndexPage filters by hackathon."""
        from django.contrib.auth.models import AnonymousUser

        hackathon1 = HackathonPageFactory(title="Hackathon 1")
        hackathon2 = HackathonPageFactory(title="Hackathon 2")

        team1 = TeamProfilePageFactory()
        team2 = TeamProfilePageFactory()

        # Create submissions for different hackathons
        sub1 = SubmissionPage(
            title="Submission for H1",
            slug="sub-h1",
            team_profile=team1,
        )
        submission_index.add_child(instance=sub1)
        sub1.hackathons.add(hackathon1)

        sub2 = SubmissionPage(
            title="Submission for H2",
            slug="sub-h2",
            team_profile=team2,
        )
        submission_index.add_child(instance=sub2)
        sub2.hackathons.add(hackathon2)

        # Filter by hackathon1
        request = rf.get(f"/?hackathon={hackathon1.id}")
        request.user = AnonymousUser()
        context = submission_index.get_context(request)

        assert len(context['submissions']) == 1
        assert context['submissions'][0].title == "Submission for H1"

    def test_filter_by_status(self, db, wagtail_root, submission_index, rf):
        """SubmissionIndexPage filters by verification status."""
        from django.contrib.auth.models import AnonymousUser

        team = TeamProfilePageFactory()

        # Create submissions with different statuses
        draft_sub = SubmissionPage(
            title="Draft Submission",
            slug="draft-sub",
            team_profile=team,
            verification_status='draft',
        )
        submission_index.add_child(instance=draft_sub)

        verified_sub = SubmissionPage(
            title="Verified Submission",
            slug="verified-sub",
            team_profile=team,
            verification_status='verified',
        )
        submission_index.add_child(instance=verified_sub)

        # Filter by verified status
        request = rf.get("/?status=verified")
        request.user = AnonymousUser()
        context = submission_index.get_context(request)

        assert len(context['submissions']) == 1
        assert context['submissions'][0].verification_status == 'verified'
