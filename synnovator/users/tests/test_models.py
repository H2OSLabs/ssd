"""
Tests for User model.
"""

import pytest
from synnovator.users.tests.factories import (
    UserFactory,
    AdminUserFactory,
    ExperiencedUserFactory,
)


class TestUserModel:
    """Tests for User model creation and basic fields."""

    def test_user_creation(self, db):
        """User can be created with valid data."""
        user = UserFactory()
        assert user.pk is not None
        assert user.username.startswith("user_")
        assert user.email

    def test_user_str_representation(self, db):
        """User __str__ returns username."""
        user = UserFactory(username="testuser")
        assert str(user) == "testuser"

    def test_user_default_values(self, db):
        """User has correct default values."""
        user = UserFactory()
        assert user.xp_points == 0
        assert user.level == 1
        assert user.reputation_score == 0
        assert user.profile_completed is False
        assert user.is_seeking_team is False

    def test_admin_user_creation(self, db):
        """Admin user has staff and superuser flags."""
        admin = AdminUserFactory()
        assert admin.is_staff is True
        assert admin.is_superuser is True

    def test_user_preferred_role_choices(self, db):
        """User preferred_role accepts valid choices."""
        hacker = UserFactory(preferred_role="hacker")
        hipster = UserFactory(preferred_role="hipster")
        hustler = UserFactory(preferred_role="hustler")
        mentor = UserFactory(preferred_role="mentor")
        flexible = UserFactory(preferred_role="any")

        assert hacker.preferred_role == "hacker"
        assert hipster.preferred_role == "hipster"
        assert hustler.preferred_role == "hustler"
        assert mentor.preferred_role == "mentor"
        assert flexible.preferred_role == "any"

    def test_user_skills_json_field(self, db):
        """User skills can be a list of strings."""
        user = UserFactory(skills=["Python", "JavaScript", "Machine Learning"])
        assert user.skills == ["Python", "JavaScript", "Machine Learning"]
        assert len(user.skills) == 3


class TestUserXPAndLevel:
    """Tests for XP and level calculation."""

    def test_calculate_level_from_xp(self, db):
        """Level is calculated correctly from XP."""
        user = UserFactory(xp_points=0)
        assert user.calculate_level() == 1

        user.xp_points = 99
        assert user.calculate_level() == 1

        user.xp_points = 100
        assert user.calculate_level() == 2

        user.xp_points = 250
        assert user.calculate_level() == 3

        user.xp_points = 1000
        assert user.calculate_level() == 11

    def test_award_xp_increases_points(self, db):
        """award_xp increases XP and updates level."""
        user = UserFactory(xp_points=0, level=1)
        user.award_xp(50)

        user.refresh_from_db()
        assert user.xp_points == 50
        assert user.level == 1

    def test_award_xp_triggers_level_up(self, db):
        """award_xp triggers level up when threshold reached."""
        user = UserFactory(xp_points=50, level=1)
        user.award_xp(60)  # Total: 110 XP

        user.refresh_from_db()
        assert user.xp_points == 110
        assert user.level == 2

    def test_award_xp_multiple_level_ups(self, db):
        """award_xp can trigger multiple level ups."""
        user = UserFactory(xp_points=0, level=1)
        user.award_xp(500)

        user.refresh_from_db()
        assert user.xp_points == 500
        assert user.level == 6


class TestUserProfile:
    """Tests for user profile fields."""

    def test_user_bio(self, db):
        """User can have a bio."""
        user = UserFactory(bio="I love hackathons and building cool stuff!")
        assert "hackathons" in user.bio

    def test_user_profile_completed(self, db):
        """User can mark profile as completed."""
        user = UserFactory(profile_completed=False)
        assert user.profile_completed is False

        user.profile_completed = True
        user.save()
        user.refresh_from_db()
        assert user.profile_completed is True

    def test_user_seeking_team(self, db):
        """User can be seeking team."""
        user = UserFactory(is_seeking_team=True)
        assert user.is_seeking_team is True

    def test_user_notification_preferences(self, db):
        """User can have notification preferences."""
        user = UserFactory(
            notification_preferences={
                "email_notifications": True,
                "push_notifications": False,
            }
        )
        assert user.notification_preferences["email_notifications"] is True
        assert user.notification_preferences["push_notifications"] is False


class TestUserVerifiedSkills:
    """Tests for get_verified_skills method."""

    def test_get_verified_skills_no_submissions(self, db):
        """User with no submissions has no verified skills."""
        user = UserFactory()
        skills = user.get_verified_skills()
        assert skills == []

    def test_get_verified_skills_with_submissions(self, db):
        """User with verified quest submissions has verified skills."""
        # This test requires Submission and Quest models
        # Will be implemented after hackathons factories are created
        pass


class TestUserAuthentication:
    """Tests for user authentication."""

    def test_user_can_authenticate(self, db, client):
        """User can authenticate with correct password."""
        user = UserFactory(username="authtest")

        login_success = client.login(username="authtest", password="password123")
        assert login_success is True

    def test_user_cannot_authenticate_wrong_password(self, db, client):
        """User cannot authenticate with wrong password."""
        user = UserFactory(username="authtest2")

        login_success = client.login(username="authtest2", password="wrongpassword")
        assert login_success is False
