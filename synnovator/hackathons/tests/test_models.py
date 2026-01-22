"""
Tests for hackathons models.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta

from synnovator.hackathons.tests.factories import (
    HackathonPageFactory,
    HackathonIndexPageFactory,
    QuestFactory,
    QuestIndexPageFactory,
    TeamFactory,
    TeamMemberFactory,
    PhaseFactory,
    ActivePhaseFactory,
    FuturePhaseFactory,
    PastPhaseFactory,
    PrizeFactory,
    SubmissionFactory,
    TeamSubmissionFactory,
    VerifiedSubmissionFactory,
    ScoredTeamFactory,
    SubmissionIndexPageFactory,
    SubmissionPageFactory,
)
from synnovator.users.tests.factories import UserFactory
from synnovator.community.tests.factories import TeamProfilePageFactory


class TestHackathonPage:
    """Tests for HackathonPage Wagtail model."""

    def test_hackathon_page_creation(self, db):
        """HackathonPage can be created in page tree."""
        hackathon = HackathonPageFactory(title="AI Challenge 2026")
        assert hackathon.pk is not None
        assert hackathon.title == "AI Challenge 2026"
        assert hackathon.live is True

    def test_hackathon_page_str(self, db):
        """HackathonPage __str__ returns title."""
        hackathon = HackathonPageFactory(title="Test Hackathon")
        assert str(hackathon) == "Test Hackathon"

    def test_hackathon_default_status(self, db):
        """HackathonPage has default draft status."""
        hackathon = HackathonPageFactory()
        assert hackathon.status == "upcoming"

    def test_hackathon_status_choices(self, db):
        """HackathonPage accepts valid status choices."""
        statuses = ["draft", "upcoming", "registration_open", "in_progress", "judging", "completed", "archived"]
        for status in statuses:
            hackathon = HackathonPageFactory(status=status)
            assert hackathon.status == status

    def test_hackathon_team_size_configuration(self, db):
        """HackathonPage team size configuration works."""
        hackathon = HackathonPageFactory(min_team_size=3, max_team_size=6)
        assert hackathon.min_team_size == 3
        assert hackathon.max_team_size == 6

    def test_hackathon_allow_solo(self, db):
        """HackathonPage can allow solo participation."""
        hackathon = HackathonPageFactory(allow_solo=True)
        assert hackathon.allow_solo is True

    def test_hackathon_required_roles(self, db):
        """HackathonPage can have required roles."""
        hackathon = HackathonPageFactory(required_roles=["hacker", "hustler"])
        assert hackathon.required_roles == ["hacker", "hustler"]


class TestHackathonPageMethods:
    """Tests for HackathonPage methods."""

    def test_get_current_phase_no_phases(self, db):
        """get_current_phase returns None when no phases exist."""
        hackathon = HackathonPageFactory()
        assert hackathon.get_current_phase() is None

    def test_get_current_phase_active(self, db):
        """get_current_phase returns active phase."""
        hackathon = HackathonPageFactory()
        active_phase = ActivePhaseFactory(hackathon=hackathon, title="Active Phase")
        FuturePhaseFactory(hackathon=hackathon, title="Future Phase")

        current = hackathon.get_current_phase()
        assert current == active_phase

    def test_get_current_phase_none_active(self, db):
        """get_current_phase returns None when no active phase."""
        hackathon = HackathonPageFactory()
        FuturePhaseFactory(hackathon=hackathon)
        PastPhaseFactory(hackathon=hackathon)

        assert hackathon.get_current_phase() is None

    def test_get_leaderboard_empty(self, db):
        """get_leaderboard returns empty queryset when no teams."""
        hackathon = HackathonPageFactory()
        leaderboard = hackathon.get_leaderboard()
        assert list(leaderboard) == []

    def test_get_leaderboard_ordered_by_score(self, db):
        """get_leaderboard returns teams ordered by score."""
        hackathon = HackathonPageFactory()
        team1 = ScoredTeamFactory(hackathon=hackathon, final_score=80, status="verified")
        team2 = ScoredTeamFactory(hackathon=hackathon, final_score=95, status="verified")
        team3 = ScoredTeamFactory(hackathon=hackathon, final_score=70, status="submitted")

        leaderboard = list(hackathon.get_leaderboard())
        assert leaderboard[0] == team2  # Highest score first
        assert leaderboard[1] == team1

    def test_get_leaderboard_excludes_forming_teams(self, db):
        """get_leaderboard excludes teams still forming."""
        hackathon = HackathonPageFactory()
        ScoredTeamFactory(hackathon=hackathon, final_score=90, status="verified")
        TeamFactory(hackathon=hackathon, status="forming")

        leaderboard = hackathon.get_leaderboard()
        assert leaderboard.count() == 1

    def test_get_leaderboard_limit(self, db):
        """get_leaderboard respects limit parameter."""
        hackathon = HackathonPageFactory()
        for i in range(15):
            ScoredTeamFactory(hackathon=hackathon, final_score=50 + i, status="verified")

        leaderboard = hackathon.get_leaderboard(limit=5)
        assert len(list(leaderboard)) == 5


class TestHackathonIndexPage:
    """Tests for HackathonIndexPage."""

    def test_hackathon_index_creation(self, db, wagtail_root):
        """HackathonIndexPage can be created."""
        index = HackathonIndexPageFactory(parent=wagtail_root)
        assert index.pk is not None
        assert index.title == "Hackathons"

    def test_hackathon_index_can_have_children(self, db, wagtail_root):
        """HackathonIndexPage can have HackathonPage children."""
        index = HackathonIndexPageFactory(parent=wagtail_root)
        hackathon1 = HackathonPageFactory(parent=index)
        hackathon2 = HackathonPageFactory(parent=index)

        children = index.get_children().specific()
        assert children.count() == 2

    def test_hackathon_index_featured_hackathon(self, db, wagtail_root):
        """HackathonIndexPage can have featured hackathon."""
        index = HackathonIndexPageFactory(parent=wagtail_root)
        hackathon = HackathonPageFactory(parent=index)

        index.featured_hackathon = hackathon
        index.save()

        index.refresh_from_db()
        assert index.featured_hackathon == hackathon


class TestQuestIndexPage:
    """Tests for QuestIndexPage."""

    def test_quest_index_creation(self, db, wagtail_root):
        """QuestIndexPage can be created."""
        index = QuestIndexPageFactory(parent=wagtail_root)
        assert index.pk is not None
        assert index.title == "Quests"

    def test_quest_index_featured_quest(self, db, wagtail_root):
        """QuestIndexPage can have featured quest."""
        index = QuestIndexPageFactory(parent=wagtail_root)
        quest = QuestFactory()

        index.featured_quest = quest
        index.save()

        index.refresh_from_db()
        assert index.featured_quest == quest

    def test_quest_index_get_context_includes_quests(self, db, wagtail_root, rf):
        """QuestIndexPage.get_context() includes active quests."""
        from django.contrib.auth.models import AnonymousUser

        index = QuestIndexPageFactory(parent=wagtail_root)
        quest1 = QuestFactory(is_active=True, title="Quest 1")
        quest2 = QuestFactory(is_active=True, title="Quest 2")
        QuestFactory(is_active=False, title="Inactive Quest")

        request = rf.get("/")
        request.user = AnonymousUser()
        context = index.get_context(request)

        assert "quests" in context
        quest_titles = [q.title for q in context["quests"]]
        assert "Quest 1" in quest_titles
        assert "Quest 2" in quest_titles
        assert "Inactive Quest" not in quest_titles

    def test_quest_index_get_context_filters_by_difficulty(self, db, wagtail_root, rf):
        """QuestIndexPage.get_context() filters quests by difficulty."""
        from django.contrib.auth.models import AnonymousUser

        index = QuestIndexPageFactory(parent=wagtail_root)
        beginner_quest = QuestFactory(is_active=True, difficulty="beginner", title="Beginner Quest")
        advanced_quest = QuestFactory(is_active=True, difficulty="advanced", title="Advanced Quest")

        request = rf.get("/", {"difficulty": ["easy"]})  # easy maps to beginner
        request.user = AnonymousUser()
        context = index.get_context(request)

        quest_titles = [q.title for q in context["quests"]]
        assert "Beginner Quest" in quest_titles
        assert "Advanced Quest" not in quest_titles

    def test_quest_index_get_context_excludes_featured(self, db, wagtail_root, rf):
        """QuestIndexPage.get_context() excludes featured quest from list."""
        from django.contrib.auth.models import AnonymousUser

        index = QuestIndexPageFactory(parent=wagtail_root)
        featured = QuestFactory(is_active=True, title="Featured Quest")
        regular = QuestFactory(is_active=True, title="Regular Quest")

        index.featured_quest = featured
        index.save()

        request = rf.get("/")
        request.user = AnonymousUser()
        context = index.get_context(request)

        assert context["featured"] == featured
        quest_titles = [q.title for q in context["quests"]]
        assert "Regular Quest" in quest_titles
        assert "Featured Quest" not in quest_titles

    def test_quest_index_get_context_pagination(self, db, wagtail_root, rf):
        """QuestIndexPage.get_context() includes pagination."""
        from django.contrib.auth.models import AnonymousUser

        index = QuestIndexPageFactory(parent=wagtail_root)
        # Create more quests than DEFAULT_PER_PAGE (8)
        for i in range(10):
            QuestFactory(is_active=True, title=f"Quest {i}")

        request = rf.get("/")
        request.user = AnonymousUser()
        context = index.get_context(request)

        assert "paginator" in context
        assert "paginator_page" in context
        assert "is_paginated" in context
        assert len(context["quests"]) <= 8  # DEFAULT_PER_PAGE

    def test_quest_index_get_context_user_stats(self, db, wagtail_root, rf):
        """QuestIndexPage.get_context() includes user stats for authenticated users."""
        from synnovator.users.tests.factories import UserFactory

        index = QuestIndexPageFactory(parent=wagtail_root)
        user = UserFactory()
        quest = QuestFactory(is_active=True, xp_reward=100)
        VerifiedSubmissionFactory(user=user, quest=quest)

        request = rf.get("/")
        request.user = user
        context = index.get_context(request)

        assert "user_stats" in context
        assert context["user_stats"]["completed_count"] == 1
        assert context["user_stats"]["total_xp"] == 100

    def test_quest_index_get_context_recommended_quests(self, db, wagtail_root, rf):
        """QuestIndexPage.get_context() includes recommended quests."""
        from synnovator.users.tests.factories import UserFactory

        index = QuestIndexPageFactory(parent=wagtail_root)
        user = UserFactory(skills=["python"])
        QuestFactory(is_active=True, difficulty="beginner", tags=["python"], title="Python Quest")
        QuestFactory(is_active=True, difficulty="beginner", tags=["javascript"], title="JS Quest")

        request = rf.get("/")
        request.user = user
        context = index.get_context(request)

        assert "recommended_quests" in context
        recommended_titles = [q.title for q in context["recommended_quests"]]
        # Should recommend quests matching user skills
        assert len(context["recommended_quests"]) > 0


class TestQuest:
    """Tests for Quest snippet model."""

    def test_quest_creation(self, db):
        """Quest can be created with valid data."""
        quest = QuestFactory()
        assert quest.pk is not None
        assert quest.title
        assert quest.quest_type in ["technical", "commercial", "operational", "mixed"]

    def test_quest_str_representation(self, db):
        """Quest __str__ returns title with difficulty."""
        quest = QuestFactory(title="Build an API", difficulty="beginner")
        assert str(quest) == "Build an API (Beginner)"

    def test_quest_type_choices(self, db):
        """Quest quest_type accepts valid choices."""
        types = ["technical", "commercial", "operational", "mixed"]
        for quest_type in types:
            quest = QuestFactory(quest_type=quest_type)
            assert quest.quest_type == quest_type

    def test_quest_difficulty_choices(self, db):
        """Quest difficulty accepts valid choices."""
        difficulties = ["beginner", "intermediate", "advanced", "expert"]
        for difficulty in difficulties:
            quest = QuestFactory(difficulty=difficulty)
            assert quest.difficulty == difficulty

    def test_quest_xp_reward(self, db):
        """Quest XP reward is positive."""
        quest = QuestFactory(xp_reward=50)
        assert quest.xp_reward == 50

    def test_quest_is_active_default(self, db):
        """Quest is active by default."""
        quest = QuestFactory()
        assert quest.is_active is True

    def test_quest_tags(self, db):
        """Quest can have tags."""
        quest = QuestFactory(tags=["python", "django", "rest-api"])
        assert quest.tags == ["python", "django", "rest-api"]

    def test_quest_get_completion_rate_no_submissions(self, db):
        """get_completion_rate returns 0 when no submissions."""
        quest = QuestFactory()
        assert quest.get_completion_rate() == 0

    def test_quest_get_completion_rate(self, db):
        """get_completion_rate calculates correctly."""
        quest = QuestFactory()
        # Create 4 submissions: 2 verified, 1 pending, 1 rejected
        SubmissionFactory(quest=quest, verification_status="verified")
        SubmissionFactory(quest=quest, verification_status="verified")
        SubmissionFactory(quest=quest, verification_status="pending")
        SubmissionFactory(quest=quest, verification_status="rejected")

        rate = quest.get_completion_rate()
        assert rate == 50.0  # 2 out of 4


class TestTeam:
    """Tests for Team model."""

    def test_team_creation(self, db):
        """Team can be created with hackathon."""
        team = TeamFactory()
        assert team.pk is not None
        assert team.hackathon is not None

    def test_team_str_representation(self, db):
        """Team __str__ returns name with hackathon."""
        hackathon = HackathonPageFactory(title="Test Hackathon")
        team = TeamFactory(name="Dream Team", hackathon=hackathon)
        assert str(team) == "Dream Team (Test Hackathon)"

    def test_team_default_status(self, db):
        """Team has default forming status."""
        team = TeamFactory()
        assert team.status == "forming"

    def test_team_status_choices(self, db):
        """Team accepts valid status choices."""
        statuses = ["forming", "ready", "submitted", "verified", "advanced", "eliminated", "disqualified"]
        for status in statuses:
            team = TeamFactory(status=status)
            assert team.status == status

    def test_team_default_scores(self, db):
        """Team has default zero scores."""
        team = TeamFactory()
        assert team.final_score == 0.0
        assert team.technical_score == 0.0
        assert team.commercial_score == 0.0
        assert team.operational_score == 0.0

    def test_team_unique_slug_per_hackathon(self, db):
        """Team slug must be unique within hackathon."""
        hackathon = HackathonPageFactory()
        TeamFactory(hackathon=hackathon, slug="unique-team")

        with pytest.raises(IntegrityError):
            TeamFactory(hackathon=hackathon, slug="unique-team")


class TestTeamMethods:
    """Tests for Team methods."""

    def test_get_leader_with_leader(self, db):
        """get_leader returns team leader."""
        team = TeamFactory()
        leader = UserFactory()
        member = UserFactory()

        TeamMemberFactory(team=team, user=leader, is_leader=True)
        TeamMemberFactory(team=team, user=member, is_leader=False)

        leader_member = team.get_leader()
        assert leader_member.user == leader

    def test_get_leader_no_leader(self, db):
        """get_leader returns None when no leader."""
        team = TeamFactory()
        member = UserFactory()
        TeamMemberFactory(team=team, user=member, is_leader=False)

        assert team.get_leader() is None

    def test_has_required_roles_no_requirements(self, db):
        """has_required_roles returns True when no requirements."""
        hackathon = HackathonPageFactory(required_roles=[])
        team = TeamFactory(hackathon=hackathon)
        TeamMemberFactory(team=team, role="hacker")

        assert team.has_required_roles() is True

    def test_has_required_roles_met(self, db):
        """has_required_roles returns True when requirements met."""
        hackathon = HackathonPageFactory(required_roles=["hacker", "hustler"])
        team = TeamFactory(hackathon=hackathon)
        TeamMemberFactory(team=team, role="hacker")
        TeamMemberFactory(team=team, role="hustler")

        assert team.has_required_roles() is True

    def test_has_required_roles_not_met(self, db):
        """has_required_roles returns False when requirements not met."""
        hackathon = HackathonPageFactory(required_roles=["hacker", "hustler"])
        team = TeamFactory(hackathon=hackathon)
        TeamMemberFactory(team=team, role="hacker")

        assert team.has_required_roles() is False

    def test_can_add_member_under_limit(self, db):
        """can_add_member returns True when under max size."""
        hackathon = HackathonPageFactory(max_team_size=5)
        team = TeamFactory(hackathon=hackathon, status="forming")
        TeamMemberFactory(team=team)
        TeamMemberFactory(team=team)

        assert team.can_add_member() is True

    def test_can_add_member_at_limit(self, db):
        """can_add_member returns False when at max size."""
        hackathon = HackathonPageFactory(max_team_size=2)
        team = TeamFactory(hackathon=hackathon, status="forming")
        TeamMemberFactory(team=team)
        TeamMemberFactory(team=team)

        assert team.can_add_member() is False

    def test_can_add_member_wrong_status(self, db):
        """can_add_member returns False when not forming."""
        team = TeamFactory(status="ready")
        assert team.can_add_member() is False


class TestTeamMember:
    """Tests for TeamMember through model."""

    def test_team_member_creation(self, db):
        """TeamMember can be created."""
        member = TeamMemberFactory()
        assert member.pk is not None
        assert member.team is not None
        assert member.user is not None

    def test_team_member_str_representation(self, db):
        """TeamMember __str__ returns user and role."""
        user = UserFactory(first_name="John", last_name="Doe")
        member = TeamMemberFactory(user=user, role="hacker", is_leader=False)
        assert "Hacker" in str(member)

    def test_team_member_leader_str(self, db):
        """TeamMember __str__ includes Leader for leaders."""
        user = UserFactory(first_name="Jane", last_name="Doe")
        member = TeamMemberFactory(user=user, role="hustler", is_leader=True)
        assert "(Leader)" in str(member)

    def test_team_member_role_choices(self, db):
        """TeamMember accepts valid role choices."""
        roles = ["hacker", "hipster", "hustler", "mentor"]
        for role in roles:
            member = TeamMemberFactory(role=role)
            assert member.role == role

    def test_team_member_unique_per_team(self, db):
        """User can only join team once."""
        team = TeamFactory()
        user = UserFactory()
        TeamMemberFactory(team=team, user=user)

        with pytest.raises(IntegrityError):
            TeamMemberFactory(team=team, user=user)

    def test_user_can_join_multiple_teams(self, db):
        """User can join different teams."""
        user = UserFactory()
        team1 = TeamFactory()
        team2 = TeamFactory()

        TeamMemberFactory(team=team1, user=user)
        TeamMemberFactory(team=team2, user=user)

        assert user.team_memberships.count() == 2


class TestPhase:
    """Tests for Phase inline model."""

    def test_phase_creation(self, db):
        """Phase can be created."""
        phase = PhaseFactory()
        assert phase.pk is not None
        assert phase.hackathon is not None

    def test_phase_str_representation(self, db):
        """Phase __str__ returns title with date."""
        phase = PhaseFactory(title="Registration")
        assert "Registration" in str(phase)

    def test_phase_is_active_true(self, db):
        """is_active returns True for current phase."""
        phase = ActivePhaseFactory()
        assert phase.is_active() is True

    def test_phase_is_active_false_future(self, db):
        """is_active returns False for future phase."""
        phase = FuturePhaseFactory()
        assert phase.is_active() is False

    def test_phase_is_active_false_past(self, db):
        """is_active returns False for past phase."""
        phase = PastPhaseFactory()
        assert phase.is_active() is False

    def test_phase_ordering(self, db):
        """Phases are ordered by order and start_date."""
        hackathon = HackathonPageFactory()
        phase3 = PhaseFactory(hackathon=hackathon, order=3)
        phase1 = PhaseFactory(hackathon=hackathon, order=1)
        phase2 = PhaseFactory(hackathon=hackathon, order=2)

        phases = list(hackathon.phases.all())
        assert phases[0] == phase1
        assert phases[1] == phase2
        assert phases[2] == phase3


class TestPhaseQuestCompletion:
    """Tests for Phase.check_quest_completion method."""

    def test_check_quest_completion_no_required(self, db):
        """Returns True when no quests required."""
        phase = PhaseFactory()
        user = UserFactory()

        is_complete, message = phase.check_quest_completion(user)
        assert is_complete is True
        assert "No quests required" in message

    def test_check_quest_completion_all_complete(self, db):
        """Returns True when all quests completed."""
        phase = PhaseFactory()
        quest = QuestFactory()
        phase.required_quests.add(quest)

        user = UserFactory()
        VerifiedSubmissionFactory(user=user, quest=quest)

        is_complete, message = phase.check_quest_completion(user)
        assert is_complete is True

    def test_check_quest_completion_missing(self, db):
        """Returns False when quests missing."""
        phase = PhaseFactory()
        quest1 = QuestFactory(title="Quest 1")
        quest2 = QuestFactory(title="Quest 2")
        phase.required_quests.add(quest1, quest2)

        user = UserFactory()
        VerifiedSubmissionFactory(user=user, quest=quest1)
        # Quest 2 not completed

        is_complete, message = phase.check_quest_completion(user)
        assert is_complete is False
        assert "Quest 2" in message


class TestPrize:
    """Tests for Prize inline model."""

    def test_prize_creation(self, db):
        """Prize can be created."""
        prize = PrizeFactory()
        assert prize.pk is not None
        assert prize.hackathon is not None

    def test_prize_str_representation(self, db):
        """Prize __str__ returns title with hackathon."""
        hackathon = HackathonPageFactory(title="Test Hackathon")
        prize = PrizeFactory(hackathon=hackathon, title="First Place")
        assert str(prize) == "First Place - Test Hackathon"

    def test_prize_ordering(self, db):
        """Prizes are ordered by rank."""
        hackathon = HackathonPageFactory()
        third = PrizeFactory(hackathon=hackathon, rank=3)
        first = PrizeFactory(hackathon=hackathon, rank=1)
        second = PrizeFactory(hackathon=hackathon, rank=2)

        prizes = list(hackathon.prizes.all())
        assert prizes[0] == first
        assert prizes[1] == second
        assert prizes[2] == third


class TestSubmission:
    """Tests for Submission model."""

    def test_submission_creation(self, db):
        """Submission can be created."""
        submission = SubmissionFactory()
        assert submission.pk is not None
        assert submission.user is not None
        assert submission.quest is not None

    def test_submission_str_representation(self, db):
        """Submission __str__ returns submitter and target."""
        user = UserFactory(first_name="John", last_name="Doe")
        quest = QuestFactory(title="Test Quest")
        submission = SubmissionFactory(user=user, quest=quest)
        assert "Submission by" in str(submission)
        assert "Test Quest" in str(submission)

    def test_submission_default_status(self, db):
        """Submission has default pending status."""
        submission = SubmissionFactory()
        assert submission.verification_status == "pending"

    def test_submission_status_choices(self, db):
        """Submission accepts valid status choices."""
        statuses = ["pending", "verified", "rejected"]
        for status in statuses:
            submission = SubmissionFactory(verification_status=status)
            assert submission.verification_status == status

    def test_team_submission(self, db):
        """Team can make hackathon submission."""
        submission = TeamSubmissionFactory()
        assert submission.team is not None
        assert submission.hackathon is not None
        assert submission.user is None
        assert submission.quest is None


class TestSubmissionValidation:
    """Tests for Submission validation."""

    def test_submission_requires_submitter(self, db):
        """Submission requires either user or team."""
        from synnovator.hackathons.models import Submission

        quest = QuestFactory()
        submission = Submission(
            user=None,
            team=None,
            quest=quest,
            submission_url="https://github.com/test"
        )

        with pytest.raises(ValidationError):
            submission.clean()

    def test_submission_requires_target(self, db):
        """Submission requires either quest or hackathon."""
        from synnovator.hackathons.models import Submission

        user = UserFactory()
        submission = Submission(
            user=user,
            quest=None,
            hackathon=None,
            submission_url="https://github.com/test"
        )

        with pytest.raises(ValidationError):
            submission.clean()

    def test_submission_requires_content(self, db):
        """Submission requires file or URL."""
        from synnovator.hackathons.models import Submission

        user = UserFactory()
        quest = QuestFactory()
        submission = Submission(
            user=user,
            quest=quest,
            submission_url="",
            submission_file=None
        )

        with pytest.raises(ValidationError):
            submission.clean()

    def test_submission_cannot_have_both_submitters(self, db):
        """Submission cannot have both user and team."""
        from synnovator.hackathons.models import Submission

        user = UserFactory()
        team = TeamFactory()
        quest = QuestFactory()
        submission = Submission(
            user=user,
            team=team,
            quest=quest,
            submission_url="https://github.com/test"
        )

        with pytest.raises(ValidationError):
            submission.clean()


# =============================================================================
# SubmissionIndexPage Tests
# =============================================================================


class TestSubmissionIndexPage:
    """Tests for SubmissionIndexPage model."""

    def test_submission_index_creation(self, db, wagtail_root):
        """SubmissionIndexPage can be created."""
        index = SubmissionIndexPageFactory(parent=wagtail_root)
        assert index.pk is not None
        assert index.title == "Submissions"

    def test_submission_index_max_count(self, db, wagtail_root):
        """Only one SubmissionIndexPage allowed per site."""
        from synnovator.hackathons.models import SubmissionIndexPage
        assert SubmissionIndexPage.max_count == 1

    def test_submission_index_filter_toggles_default(self, db, wagtail_root):
        """Filter toggles are enabled by default."""
        index = SubmissionIndexPageFactory(parent=wagtail_root)
        assert index.enable_hackathon_filter is True
        assert index.enable_date_filter is True
        assert index.enable_submitter_filter is True
        assert index.enable_team_filter is True
        assert index.enable_status_filter is True

    def test_submission_index_filter_toggles_configurable(self, db, wagtail_root):
        """Filter toggles can be disabled."""
        index = SubmissionIndexPageFactory(
            parent=wagtail_root,
            enable_hackathon_filter=False,
            enable_date_filter=False
        )
        assert index.enable_hackathon_filter is False
        assert index.enable_date_filter is False

    def test_submission_index_default_hackathon(self, db, wagtail_root):
        """SubmissionIndexPage can have default hackathon filter."""
        index = SubmissionIndexPageFactory(parent=wagtail_root)
        hackathon = HackathonPageFactory()

        index.default_hackathon = hackathon
        index.save()

        index.refresh_from_db()
        assert index.default_hackathon == hackathon

    def test_submission_index_default_status(self, db, wagtail_root):
        """SubmissionIndexPage can have default status filter."""
        index = SubmissionIndexPageFactory(
            parent=wagtail_root,
            default_status="verified"
        )
        assert index.default_status == "verified"

    def test_submission_index_get_context_includes_submissions(self, db, wagtail_root, rf):
        """SubmissionIndexPage.get_context() includes submissions."""
        from django.contrib.auth.models import AnonymousUser

        index = SubmissionIndexPageFactory(parent=wagtail_root)
        submission1 = SubmissionPageFactory(parent=index, title="Submission 1")
        submission2 = SubmissionPageFactory(parent=index, title="Submission 2")

        request = rf.get("/")
        request.user = AnonymousUser()
        context = index.get_context(request)

        assert "submissions" in context
        submission_titles = [s.title for s in context["submissions"]]
        assert "Submission 1" in submission_titles
        assert "Submission 2" in submission_titles

    def test_submission_index_get_context_filters_by_hackathon(self, db, wagtail_root, rf):
        """SubmissionIndexPage.get_context() filters by hackathon."""
        from django.contrib.auth.models import AnonymousUser

        index = SubmissionIndexPageFactory(parent=wagtail_root)
        hackathon1 = HackathonPageFactory(title="Hackathon 1")
        hackathon2 = HackathonPageFactory(title="Hackathon 2")

        submission1 = SubmissionPageFactory(parent=index, title="Sub for H1")
        submission1.hackathons.add(hackathon1)
        submission2 = SubmissionPageFactory(parent=index, title="Sub for H2")
        submission2.hackathons.add(hackathon2)

        request = rf.get("/", {"hackathon": str(hackathon1.id)})
        request.user = AnonymousUser()
        context = index.get_context(request)

        submission_titles = [s.title for s in context["submissions"]]
        assert "Sub for H1" in submission_titles
        assert "Sub for H2" not in submission_titles

    def test_submission_index_get_context_filters_by_status(self, db, wagtail_root, rf):
        """SubmissionIndexPage.get_context() filters by status."""
        from django.contrib.auth.models import AnonymousUser

        index = SubmissionIndexPageFactory(parent=wagtail_root)
        SubmissionPageFactory(parent=index, title="Draft", verification_status="draft")
        SubmissionPageFactory(parent=index, title="Verified", verification_status="verified")

        request = rf.get("/", {"status": "verified"})
        request.user = AnonymousUser()
        context = index.get_context(request)

        submission_titles = [s.title for s in context["submissions"]]
        assert "Verified" in submission_titles
        assert "Draft" not in submission_titles

    def test_submission_index_get_context_available_filters(self, db, wagtail_root, rf):
        """SubmissionIndexPage.get_context() includes available filters."""
        from django.contrib.auth.models import AnonymousUser

        index = SubmissionIndexPageFactory(parent=wagtail_root)
        HackathonPageFactory()

        request = rf.get("/")
        request.user = AnonymousUser()
        context = index.get_context(request)

        assert "available_filters" in context
        assert "hackathons" in context["available_filters"]
        assert "statuses" in context["available_filters"]


# =============================================================================
# SubmissionPage Tests
# =============================================================================


class TestSubmissionPage:
    """Tests for SubmissionPage model."""

    def test_submission_page_creation(self, db, wagtail_root):
        """SubmissionPage can be created."""
        index = SubmissionIndexPageFactory(parent=wagtail_root)
        submission = SubmissionPageFactory(parent=index, title="My Project")
        assert submission.pk is not None
        assert submission.title == "My Project"

    def test_submission_page_individual_submitter(self, db, wagtail_root):
        """SubmissionPage can have individual submitter."""
        index = SubmissionIndexPageFactory(parent=wagtail_root)
        user = UserFactory()
        submission = SubmissionPageFactory(parent=index, submitter=user, team_profile=None)
        assert submission.submitter == user
        assert submission.team_profile is None

    def test_submission_page_team_submitter(self, db, wagtail_root):
        """SubmissionPage can have team submitter."""
        index = SubmissionIndexPageFactory(parent=wagtail_root)
        team = TeamProfilePageFactory()
        submission = SubmissionPageFactory(parent=index, submitter=None, team_profile=team)
        assert submission.team_profile == team
        assert submission.submitter is None

    def test_submission_page_hackathons_m2m(self, db, wagtail_root):
        """SubmissionPage can be associated with multiple hackathons."""
        index = SubmissionIndexPageFactory(parent=wagtail_root)
        hackathon1 = HackathonPageFactory(title="Hackathon 1")
        hackathon2 = HackathonPageFactory(title="Hackathon 2")

        submission = SubmissionPageFactory(parent=index)
        submission.hackathons.add(hackathon1, hackathon2)

        assert submission.hackathons.count() == 2
        assert hackathon1 in submission.hackathons.all()
        assert hackathon2 in submission.hackathons.all()

    def test_submission_page_get_hackathons(self, db, wagtail_root):
        """get_hackathons returns all associated hackathons."""
        index = SubmissionIndexPageFactory(parent=wagtail_root)
        hackathon = HackathonPageFactory()

        submission = SubmissionPageFactory(parent=index)
        submission.hackathons.add(hackathon)

        hackathons = submission.get_hackathons()
        assert hackathon in hackathons

    def test_submission_page_get_primary_hackathon(self, db, wagtail_root):
        """get_primary_hackathon returns first hackathon."""
        index = SubmissionIndexPageFactory(parent=wagtail_root)
        hackathon = HackathonPageFactory()

        submission = SubmissionPageFactory(parent=index)
        submission.hackathons.add(hackathon)

        assert submission.get_primary_hackathon() == hackathon

    def test_submission_page_get_submitter_display_individual(self, db, wagtail_root):
        """get_submitter_display returns user name for individual."""
        index = SubmissionIndexPageFactory(parent=wagtail_root)
        user = UserFactory(first_name="John", last_name="Doe")
        submission = SubmissionPageFactory(parent=index, submitter=user)

        assert "John Doe" in submission.get_submitter_display()

    def test_submission_page_get_submitter_display_team(self, db, wagtail_root):
        """get_submitter_display returns team name for team."""
        index = SubmissionIndexPageFactory(parent=wagtail_root)
        team = TeamProfilePageFactory(title="Dream Team")
        submission = SubmissionPageFactory(parent=index, submitter=None, team_profile=team)

        assert submission.get_submitter_display() == "Dream Team"

    def test_submission_page_verification_status_choices(self, db, wagtail_root):
        """SubmissionPage accepts valid verification status choices."""
        index = SubmissionIndexPageFactory(parent=wagtail_root)
        statuses = ["draft", "submitted", "under_review", "verified", "rejected", "needs_revision"]
        for status in statuses:
            submission = SubmissionPageFactory(parent=index, verification_status=status)
            assert submission.verification_status == status

    def test_submission_page_submit_method(self, db, wagtail_root):
        """submit() marks submission as submitted with timestamp."""
        index = SubmissionIndexPageFactory(parent=wagtail_root)
        submission = SubmissionPageFactory(parent=index, verification_status="draft")

        submission.submit()

        submission.refresh_from_db()
        assert submission.verification_status == "submitted"
        assert submission.submitted_at is not None

    def test_submission_page_verify_method(self, db, wagtail_root):
        """verify() marks submission as verified with score and feedback."""
        index = SubmissionIndexPageFactory(parent=wagtail_root)
        submission = SubmissionPageFactory(parent=index, verification_status="submitted")
        reviewer = UserFactory()

        submission.verify(reviewer, score=85.5, feedback="Great work!")

        submission.refresh_from_db()
        assert submission.verification_status == "verified"
        assert submission.score == 85.5
        assert submission.feedback == "Great work!"
        assert submission.verified_by == reviewer
        assert submission.verified_at is not None

    def test_submission_page_reject_method(self, db, wagtail_root):
        """reject() marks submission as rejected with feedback."""
        index = SubmissionIndexPageFactory(parent=wagtail_root)
        submission = SubmissionPageFactory(parent=index, verification_status="submitted")
        reviewer = UserFactory()

        submission.reject(reviewer, feedback="Does not meet requirements.")

        submission.refresh_from_db()
        assert submission.verification_status == "rejected"
        assert submission.feedback == "Does not meet requirements."
        assert submission.verified_by == reviewer

    def test_submission_page_user_can_edit_submitter(self, db, wagtail_root):
        """user_can_edit returns True for submitter."""
        index = SubmissionIndexPageFactory(parent=wagtail_root)
        user = UserFactory()
        submission = SubmissionPageFactory(parent=index, submitter=user)

        assert submission.user_can_edit(user) is True

    def test_submission_page_user_can_edit_non_submitter(self, db, wagtail_root):
        """user_can_edit returns False for non-submitter."""
        index = SubmissionIndexPageFactory(parent=wagtail_root)
        user = UserFactory()
        other_user = UserFactory()
        submission = SubmissionPageFactory(parent=index, submitter=user)

        assert submission.user_can_edit(other_user) is False

    def test_submission_page_user_can_edit_superuser(self, db, wagtail_root):
        """user_can_edit returns True for superuser."""
        index = SubmissionIndexPageFactory(parent=wagtail_root)
        user = UserFactory()
        superuser = UserFactory(is_superuser=True)
        submission = SubmissionPageFactory(parent=index, submitter=user)

        assert submission.user_can_edit(superuser) is True


class TestSubmissionPageValidation:
    """Tests for SubmissionPage validation."""

    def test_submission_page_requires_submitter(self, db, wagtail_root):
        """SubmissionPage requires either submitter or team_profile."""
        from synnovator.hackathons.models import SubmissionPage

        index = SubmissionIndexPageFactory(parent=wagtail_root)
        submission = SubmissionPage(
            title="Test",
            slug="test",
            submitter=None,
            team_profile=None
        )

        with pytest.raises(ValidationError):
            submission.clean()

    def test_submission_page_cannot_have_both_submitters(self, db, wagtail_root):
        """SubmissionPage cannot have both submitter and team_profile."""
        from synnovator.hackathons.models import SubmissionPage

        index = SubmissionIndexPageFactory(parent=wagtail_root)
        user = UserFactory()
        team = TeamProfilePageFactory()

        submission = SubmissionPage(
            title="Test",
            slug="test",
            submitter=user,
            team_profile=team
        )

        with pytest.raises(ValidationError):
            submission.clean()


# =============================================================================
# HackathonPage Submission Validation Tests
# =============================================================================


class TestHackathonPageSubmissionValidation:
    """Tests for HackathonPage submission validation methods."""

    def test_can_submit_default_allows_both(self, db):
        """Default hackathon allows both individual and team submissions."""
        hackathon = HackathonPageFactory(
            submission_type="both",
            require_registration=False,
            restrict_to_submission_phase=False
        )
        user = UserFactory()

        can_submit, reason = hackathon.can_submit(user=user)
        assert can_submit is True

    def test_can_submit_individual_only_rejects_team(self, db):
        """Individual-only hackathon rejects team submission."""
        hackathon = HackathonPageFactory(submission_type="individual", require_registration=False)
        team = TeamProfilePageFactory()

        can_submit, reason = hackathon.can_submit(team_profile=team)
        assert can_submit is False
        assert "individual" in reason.lower()

    def test_can_submit_team_only_rejects_individual(self, db):
        """Team-only hackathon rejects individual submission."""
        hackathon = HackathonPageFactory(submission_type="team", require_registration=False)
        user = UserFactory()

        can_submit, reason = hackathon.can_submit(user=user)
        assert can_submit is False
        assert "team" in reason.lower()

    def test_can_submit_requires_registration(self, db):
        """Hackathon requiring registration rejects unregistered users."""
        hackathon = HackathonPageFactory(
            submission_type="both",
            require_registration=True
        )
        user = UserFactory()

        can_submit, reason = hackathon.can_submit(user=user)
        assert can_submit is False
        assert "register" in reason.lower()

    def test_can_submit_max_submissions_reached(self, db, wagtail_root):
        """Hackathon rejects when max submissions reached."""
        hackathon = HackathonPageFactory(
            submission_type="both",
            require_registration=False,
            max_submissions_per_participant=1
        )
        user = UserFactory()

        # Create existing submission
        index = SubmissionIndexPageFactory(parent=wagtail_root)
        submission = SubmissionPageFactory(parent=index, submitter=user)
        submission.hackathons.add(hackathon)

        can_submit, reason = hackathon.can_submit(user=user)
        assert can_submit is False
        assert "maximum" in reason.lower()

    def test_can_submit_unlimited_submissions(self, db, wagtail_root):
        """Hackathon with max=0 allows unlimited submissions."""
        hackathon = HackathonPageFactory(
            submission_type="both",
            require_registration=False,
            max_submissions_per_participant=0,
            restrict_to_submission_phase=False
        )
        user = UserFactory()

        # Create existing submissions
        index = SubmissionIndexPageFactory(parent=wagtail_root)
        for _ in range(5):
            submission = SubmissionPageFactory(parent=index, submitter=user)
            submission.hackathons.add(hackathon)

        can_submit, reason = hackathon.can_submit(user=user)
        assert can_submit is True

    def test_can_submit_phase_restriction(self, db):
        """Hackathon with phase restriction rejects outside submission phase."""
        hackathon = HackathonPageFactory(
            submission_type="both",
            require_registration=False,
            restrict_to_submission_phase=True,
            status="draft"  # Not in submission phase
        )
        user = UserFactory()

        # No phases defined, status is draft
        can_submit, reason = hackathon.can_submit(user=user)
        assert can_submit is False
        assert "closed" in reason.lower()

    def test_can_submit_phase_restriction_in_progress(self, db):
        """Hackathon in progress allows submission."""
        hackathon = HackathonPageFactory(
            submission_type="both",
            require_registration=False,
            restrict_to_submission_phase=True,
            status="in_progress"
        )
        user = UserFactory()

        can_submit, reason = hackathon.can_submit(user=user)
        assert can_submit is True

    def test_can_submit_late_submission_allowed(self, db):
        """Hackathon with late submission allows after deadline."""
        hackathon = HackathonPageFactory(
            submission_type="both",
            require_registration=False,
            restrict_to_submission_phase=True,
            allow_late_submission=True,
            status="judging"  # Past submission phase
        )
        user = UserFactory()

        can_submit, reason = hackathon.can_submit(user=user)
        assert can_submit is True
        assert "late" in reason.lower()

    def test_get_submission_count_individual(self, db, wagtail_root):
        """get_submission_count returns count for individual user."""
        hackathon = HackathonPageFactory()
        user = UserFactory()

        index = SubmissionIndexPageFactory(parent=wagtail_root)
        submission = SubmissionPageFactory(parent=index, submitter=user)
        submission.hackathons.add(hackathon)

        count = hackathon.get_submission_count(user=user)
        assert count == 1

    def test_get_submission_count_team(self, db, wagtail_root):
        """get_submission_count returns count for team."""
        hackathon = HackathonPageFactory()
        team = TeamProfilePageFactory()

        index = SubmissionIndexPageFactory(parent=wagtail_root)
        submission = SubmissionPageFactory(parent=index, submitter=None, team_profile=team)
        submission.hackathons.add(hackathon)

        count = hackathon.get_submission_count(team_profile=team)
        assert count == 1

    def test_is_submission_open_no_phases(self, db):
        """is_submission_open checks status when no phases."""
        hackathon = HackathonPageFactory(status="in_progress")
        assert hackathon.is_submission_open() is True

        hackathon.status = "draft"
        hackathon.save()
        assert hackathon.is_submission_open() is False

    def test_is_submission_open_with_submission_phase(self, db):
        """is_submission_open detects submission phase."""
        hackathon = HackathonPageFactory(status="in_progress")
        ActivePhaseFactory(hackathon=hackathon, title="Submission Phase")

        assert hackathon.is_submission_open() is True

    def test_is_submission_open_with_hacking_phase(self, db):
        """is_submission_open detects hacking phase."""
        hackathon = HackathonPageFactory(status="in_progress")
        ActivePhaseFactory(hackathon=hackathon, title="Hacking Period")

        assert hackathon.is_submission_open() is True

    def test_get_submissions_returns_associated(self, db, wagtail_root):
        """get_submissions returns submissions associated with hackathon."""
        hackathon = HackathonPageFactory()

        index = SubmissionIndexPageFactory(parent=wagtail_root)
        submission1 = SubmissionPageFactory(parent=index, title="Associated")
        submission1.hackathons.add(hackathon)

        submission2 = SubmissionPageFactory(parent=index, title="Not Associated")

        submissions = hackathon.get_submissions()
        assert submission1 in submissions
        assert submission2 not in submissions
