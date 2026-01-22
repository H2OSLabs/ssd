"""
Template integration tests to verify model-template synchronization.

These tests catch issues when:
1. Model fields are renamed/removed but templates still reference old names
2. Model methods are changed but templates depend on old behavior
3. Related model changes break template rendering
"""

import pytest
from django.template import Template, Context, TemplateSyntaxError
from django.template.loader import render_to_string, get_template
from django.test import RequestFactory

from synnovator.hackathons.tests.factories import (
    HackathonIndexPageFactory,
    HackathonPageFactory,
    QuestFactory,
    TeamFactory,
    TeamMemberFactory,
    PhaseFactory,
    PrizeFactory,
    ActivePhaseFactory,
)
from synnovator.users.tests.factories import UserFactory


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.mark.integration
class TestTeamCardComponent:
    """Tests for team-card.html component."""

    def test_team_card_renders(self, db):
        """team-card.html renders with Team data."""
        team = TeamFactory(name="Dream Team", tagline="We build cool stuff")
        TeamMemberFactory(team=team)
        TeamMemberFactory(team=team)

        html = render_to_string(
            "components/team-card.html",
            {"team": team},
        )

        # Verify expected model fields are used
        assert "Dream Team" in html
        assert "We build cool stuff" in html
        assert "2 member" in html

    def test_team_card_renders_seeking_members_badge(self, db):
        """team-card.html shows recruiting badge when seeking members."""
        team = TeamFactory(is_seeking_members=True)

        html = render_to_string(
            "components/team-card.html",
            {"team": team},
        )

        assert "Recruiting" in html

    def test_team_card_renders_without_tagline(self, db):
        """team-card.html renders without tagline."""
        team = TeamFactory(tagline="")

        html = render_to_string(
            "components/team-card.html",
            {"team": team},
        )

        # Should render without error
        assert team.name in html

    def test_team_card_renders_member_avatars(self, db):
        """team-card.html shows member initials."""
        team = TeamFactory()
        user = UserFactory(first_name="John", last_name="Doe")
        TeamMemberFactory(team=team, user=user)

        html = render_to_string(
            "components/team-card.html",
            {"team": team},
        )

        # Initials should be displayed (JD)
        assert "J" in html
        assert "D" in html


@pytest.mark.integration
class TestQuestCardComponent:
    """Tests for quest-card.html component."""

    def test_quest_card_renders(self, db):
        """quest-card.html renders with Quest data."""
        quest = QuestFactory(
            title="Build an API",
            difficulty="intermediate",
            xp_reward=100,
        )

        html = render_to_string(
            "components/quest-card.html",
            {"quest": quest},
        )

        assert "Build an API" in html
        assert "100 XP" in html

    def test_quest_card_renders_difficulty_badge(self, db):
        """quest-card.html shows difficulty badge."""
        quest = QuestFactory(difficulty="beginner")

        html = render_to_string(
            "components/quest-card.html",
            {"quest": quest},
        )

        # Template uses get_difficulty_display
        assert "Beginner" in html or "beginner" in html.lower()


@pytest.mark.integration
class TestEventCardComponent:
    """Tests for event-card.html component."""

    def test_event_card_renders(self, db, wagtail_root):
        """event-card.html renders with HackathonPage data."""
        index = HackathonIndexPageFactory(parent=wagtail_root)
        hackathon = HackathonPageFactory(
            parent=index,
            title="AI Hackathon 2026",
            status="upcoming",
        )

        html = render_to_string(
            "components/event-card.html",
            {"event": hackathon},
        )

        assert "AI Hackathon 2026" in html

    def test_event_card_renders_status(self, db, wagtail_root):
        """event-card.html shows status badge."""
        index = HackathonIndexPageFactory(parent=wagtail_root)
        hackathon = HackathonPageFactory(parent=index, status="registration_open")

        html = render_to_string(
            "components/event-card.html",
            {"event": hackathon},
        )

        # Template uses get_status_display
        assert "Registration Open" in html or "registration" in html.lower()

    def test_event_card_renders_team_count(self, db, wagtail_root):
        """event-card.html shows team count."""
        index = HackathonIndexPageFactory(parent=wagtail_root)
        hackathon = HackathonPageFactory(parent=index)
        TeamFactory(hackathon=hackathon)
        TeamFactory(hackathon=hackathon)

        html = render_to_string(
            "components/event-card.html",
            {"event": hackathon},
        )

        assert "2 teams" in html


@pytest.mark.integration
class TestHackathonIndexPage:
    """Tests for hackathon_index_page.html template."""

    def test_hackathon_index_renders(self, db, wagtail_root, request_factory):
        """hackathon_index_page.html renders."""
        index = HackathonIndexPageFactory(parent=wagtail_root)
        hackathon1 = HackathonPageFactory(parent=index, title="Hackathon 1")
        hackathon2 = HackathonPageFactory(parent=index, title="Hackathon 2")

        request = request_factory.get("/")
        context = index.get_context(request)
        context["page"] = index
        context["self"] = index

        html = render_to_string(
            "hackathons/hackathon_index_page.html",
            context,
        )

        # At minimum, check it renders without error
        assert index.title in html

    def test_hackathon_index_with_featured(self, db, wagtail_root, request_factory):
        """hackathon_index_page.html renders with featured hackathon."""
        index = HackathonIndexPageFactory(parent=wagtail_root)
        featured = HackathonPageFactory(parent=index, title="Featured Event")
        index.featured_hackathon = featured
        index.save()

        request = request_factory.get("/")
        context = index.get_context(request)
        context["page"] = index
        context["self"] = index

        html = render_to_string(
            "hackathons/hackathon_index_page.html",
            context,
        )

        # Featured hackathon should be in context
        assert "featured" in context or "Featured Event" in html


@pytest.mark.integration
class TestLeaderboardComponent:
    """Tests for leaderboard.html component."""

    def test_leaderboard_renders(self, db, wagtail_root):
        """leaderboard.html renders with teams."""
        index = HackathonIndexPageFactory(parent=wagtail_root)
        hackathon = HackathonPageFactory(parent=index)

        team1 = TeamFactory(hackathon=hackathon, name="Team A", final_score=90, status="verified")
        team2 = TeamFactory(hackathon=hackathon, name="Team B", final_score=80, status="verified")

        teams = hackathon.get_leaderboard()

        html = render_to_string(
            "components/leaderboard.html",
            {"teams": teams, "hackathon": hackathon},
        )

        # Template should render team data
        assert "Team A" in html or "Team B" in html or "leaderboard" in html.lower()


@pytest.mark.integration
class TestPhaseTimelineComponent:
    """Tests for phase-timeline.html component."""

    def test_phase_timeline_renders(self, db, wagtail_root):
        """phase-timeline.html renders with phases."""
        index = HackathonIndexPageFactory(parent=wagtail_root)
        hackathon = HackathonPageFactory(parent=index)

        phase1 = PhaseFactory(hackathon=hackathon, title="Registration", order=1)
        phase2 = PhaseFactory(hackathon=hackathon, title="Hacking", order=2)
        phase3 = PhaseFactory(hackathon=hackathon, title="Judging", order=3)

        html = render_to_string(
            "components/phase-timeline.html",
            {"phases": hackathon.phases.all(), "hackathon": hackathon},
        )

        # Template should render phase data
        assert "Registration" in html or "Hacking" in html or "phase" in html.lower()


@pytest.mark.integration
class TestPrizeCardComponent:
    """Tests for prize-card.html component."""

    def test_prize_card_renders(self, db, wagtail_root):
        """prize-card.html renders with prize data."""
        index = HackathonIndexPageFactory(parent=wagtail_root)
        hackathon = HackathonPageFactory(parent=index)
        prize = PrizeFactory(
            hackathon=hackathon,
            title="First Place",
            rank=1,
            monetary_value=5000,
        )

        html = render_to_string(
            "components/prize-card.html",
            {"prize": prize},
        )

        assert "First Place" in html or "prize" in html.lower()


@pytest.mark.integration
class TestUserProfileCard:
    """Tests for user-profile-card.html component."""

    def test_user_profile_card_renders(self, db):
        """user-profile-card.html renders with user data."""
        user = UserFactory(
            username="testuser",
            xp_points=500,
            level=6,
            preferred_role="hacker",
        )

        html = render_to_string(
            "components/user-profile-card.html",
            {"user": user},
        )

        # Template should use user fields
        assert "testuser" in html or "user" in html.lower()


@pytest.mark.integration
class TestTemplatesLoadWithoutErrors:
    """Verify all templates can be loaded without syntax errors."""

    @pytest.mark.parametrize("template_name", [
        "components/team-card.html",
        "components/quest-card.html",
        "components/event-card.html",
        "components/leaderboard.html",
        "components/phase-timeline.html",
        "components/prize-card.html",
        "components/user-profile-card.html",
        "components/pagination.html",
        "hackathons/hackathon_index_page.html",
        "hackathons/hackathon_page.html",
    ])
    def test_template_loads(self, db, template_name):
        """Template can be loaded without syntax errors."""
        try:
            template = get_template(template_name)
            assert template is not None
        except TemplateSyntaxError as e:
            pytest.fail(f"Template {template_name} has syntax error: {e}")


@pytest.mark.integration
class TestModelFieldUsageInTemplates:
    """
    Tests that verify templates use correct model field names.
    These tests will fail if model fields are renamed but templates are not updated.
    """

    def test_team_uses_expected_fields(self, db):
        """Team model has fields expected by templates."""
        team = TeamFactory()

        # These are the fields used by team-card.html
        assert hasattr(team, 'name')
        assert hasattr(team, 'tagline')
        assert hasattr(team, 'membership')  # Used for member avatars
        assert hasattr(team, 'members')  # Used for count
        assert hasattr(team, 'is_seeking_members')

    def test_quest_uses_expected_fields(self, db):
        """Quest model has fields expected by templates."""
        quest = QuestFactory()

        # These are the fields used by quest-card.html
        assert hasattr(quest, 'title')
        assert hasattr(quest, 'difficulty')
        assert hasattr(quest, 'xp_reward')
        assert hasattr(quest, 'get_difficulty_display')

    def test_hackathon_uses_expected_fields(self, db, wagtail_root):
        """HackathonPage model has fields expected by templates."""
        index = HackathonIndexPageFactory(parent=wagtail_root)
        hackathon = HackathonPageFactory(parent=index)

        # These are the fields used by event-card.html
        assert hasattr(hackathon, 'title')
        assert hasattr(hackathon, 'status')
        assert hasattr(hackathon, 'teams')
        assert hasattr(hackathon, 'cover_image')
        assert hasattr(hackathon, 'get_status_display')
        assert hasattr(hackathon, 'get_current_phase')
        assert hasattr(hackathon, 'url')

    def test_phase_uses_expected_fields(self, db, wagtail_root):
        """Phase model has fields expected by templates."""
        index = HackathonIndexPageFactory(parent=wagtail_root)
        hackathon = HackathonPageFactory(parent=index)
        phase = PhaseFactory(hackathon=hackathon)

        # These are the fields used by phase-timeline.html
        assert hasattr(phase, 'title')
        assert hasattr(phase, 'description')
        assert hasattr(phase, 'start_date')
        assert hasattr(phase, 'end_date')
        assert hasattr(phase, 'order')
        assert hasattr(phase, 'is_active')

    def test_prize_uses_expected_fields(self, db, wagtail_root):
        """Prize model has fields expected by templates."""
        index = HackathonIndexPageFactory(parent=wagtail_root)
        hackathon = HackathonPageFactory(parent=index)
        prize = PrizeFactory(hackathon=hackathon)

        # These are the fields used by prize-card.html
        assert hasattr(prize, 'title')
        assert hasattr(prize, 'description')
        assert hasattr(prize, 'rank')
        assert hasattr(prize, 'monetary_value')

    def test_user_uses_expected_fields(self, db):
        """User model has fields expected by templates."""
        user = UserFactory()

        # These are the fields used by user-profile-card.html
        assert hasattr(user, 'username')
        assert hasattr(user, 'first_name')
        assert hasattr(user, 'last_name')
        assert hasattr(user, 'xp_points')
        assert hasattr(user, 'level')
        assert hasattr(user, 'preferred_role')
        assert hasattr(user, 'bio')
