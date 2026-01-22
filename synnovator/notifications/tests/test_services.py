"""
Tests for NotificationService.
"""

import pytest
from wagtail.models import Site

from synnovator.notifications.models import Notification, NotificationSettings
from synnovator.notifications.services import NotificationService
from synnovator.users.tests.factories import UserFactory


@pytest.fixture
def site(db):
    """Get the default site."""
    return Site.objects.get(is_default_site=True)


@pytest.fixture
def notification_settings(site):
    """Create NotificationSettings for the site."""
    settings, _ = NotificationSettings.objects.get_or_create(site=site)
    return settings


class TestNotificationService:
    """Tests for NotificationService."""

    def test_service_initialization(self, db):
        """Service can be initialized without arguments."""
        service = NotificationService()
        assert service is not None

    def test_service_initialization_with_site(self, site):
        """Service can be initialized with a specific site."""
        service = NotificationService(site=site)
        assert service.site == site

    def test_settings_lazy_loading(self, site, notification_settings):
        """Settings are lazily loaded from site."""
        service = NotificationService(site=site)
        # Access settings property
        settings = service.settings
        assert settings is not None
        assert settings.site == site


class TestShouldNotify:
    """Tests for NotificationService.should_notify method."""

    def test_should_notify_default_in_app(self, db):
        """Default behavior allows in-app notifications."""
        user = UserFactory()
        service = NotificationService()

        result = service.should_notify(user, 'team_invitation', 'in_app')
        assert result is True

    def test_should_notify_default_email_disabled(self, db):
        """Default behavior disables email notifications."""
        user = UserFactory()
        service = NotificationService()

        result = service.should_notify(user, 'team_invitation', 'email')
        assert result is False

    def test_should_notify_user_disabled_type(self, db):
        """User can disable specific notification types."""
        user = UserFactory()
        user.set_notification_preference('team_invitation', 'in_app', False)

        service = NotificationService()
        result = service.should_notify(user, 'team_invitation', 'in_app')
        assert result is False

    def test_should_notify_user_enabled_email(self, db):
        """User can enable email for specific types."""
        user = UserFactory()
        user.set_notification_preference('team_invitation', 'email', True)

        service = NotificationService()
        result = service.should_notify(user, 'team_invitation', 'email')
        assert result is True

    def test_should_notify_global_type_disabled(self, site, notification_settings):
        """Global settings can disable notification types."""
        notification_settings.enabled_types = {'team_invitation': False}
        notification_settings.save()

        user = UserFactory()
        service = NotificationService(site=site)

        result = service.should_notify(user, 'team_invitation', 'in_app')
        assert result is False

    def test_should_notify_content_owner_disabled(self, site, notification_settings):
        """Content owner notifications can be disabled globally."""
        notification_settings.notify_content_owner = False
        notification_settings.save()

        user = UserFactory()
        service = NotificationService(site=site)

        result = service.should_notify(user, 'hackathon_created', 'in_app', is_content_owner=True)
        assert result is False

    def test_should_notify_content_owner_enabled(self, site, notification_settings):
        """Content owner notifications enabled by default."""
        notification_settings.notify_content_owner = True
        notification_settings.save()

        user = UserFactory()
        service = NotificationService(site=site)

        result = service.should_notify(user, 'hackathon_created', 'in_app', is_content_owner=True)
        assert result is True


class TestCreateNotification:
    """Tests for NotificationService.create_notification method."""

    def test_create_notification_success(self, db):
        """Notification is created when preferences allow."""
        user = UserFactory()
        service = NotificationService()

        notification = service.create_notification(
            recipient=user,
            notification_type='team_invitation',
            title='Team Invitation',
            message='You have been invited to join Team X',
        )

        assert notification is not None
        assert notification.recipient == user
        assert notification.notification_type == 'team_invitation'
        assert notification.title == 'Team Invitation'

    def test_create_notification_with_metadata(self, db):
        """Notification can include metadata."""
        user = UserFactory()
        service = NotificationService()

        notification = service.create_notification(
            recipient=user,
            notification_type='team_invitation',
            title='Team Invitation',
            message='You have been invited',
            metadata={'team_id': 123, 'inviter_id': 456}
        )

        assert notification.metadata['team_id'] == 123
        assert notification.metadata['inviter_id'] == 456

    def test_create_notification_with_link_url(self, db):
        """Notification can include link URL."""
        user = UserFactory()
        service = NotificationService()

        notification = service.create_notification(
            recipient=user,
            notification_type='team_invitation',
            title='Team Invitation',
            message='You have been invited',
            link_url='https://example.com/teams/123/'
        )

        assert notification.link_url == 'https://example.com/teams/123/'

    def test_create_notification_blocked_by_user_preference(self, db):
        """Notification not created when user disables type."""
        user = UserFactory()
        user.set_notification_preference('team_invitation', 'in_app', False)

        service = NotificationService()
        notification = service.create_notification(
            recipient=user,
            notification_type='team_invitation',
            title='Team Invitation',
            message='You have been invited',
        )

        assert notification is None
        assert Notification.objects.filter(recipient=user).count() == 0

    def test_create_notification_blocked_by_global_settings(self, site, notification_settings):
        """Notification not created when globally disabled."""
        notification_settings.enabled_types = {'team_invitation': False}
        notification_settings.save()

        user = UserFactory()
        service = NotificationService(site=site)

        notification = service.create_notification(
            recipient=user,
            notification_type='team_invitation',
            title='Team Invitation',
            message='You have been invited',
        )

        assert notification is None

    def test_create_notification_content_owner_blocked(self, site, notification_settings):
        """Content owner notification blocked when setting disabled."""
        notification_settings.notify_content_owner = False
        notification_settings.save()

        user = UserFactory()
        service = NotificationService(site=site)

        notification = service.create_notification(
            recipient=user,
            notification_type='hackathon_created',
            title='Hackathon Created',
            message='Your hackathon was created',
            is_content_owner=True,
        )

        assert notification is None


class TestNotifyUsers:
    """Tests for NotificationService.notify_users method."""

    def test_notify_multiple_users(self, db):
        """Notifications created for multiple users."""
        users = [UserFactory() for _ in range(3)]
        service = NotificationService()

        notifications = service.notify_users(
            users=users,
            notification_type='system_announcement',
            title='System Update',
            message='The system has been updated.',
        )

        assert len(notifications) == 3
        for user in users:
            assert Notification.objects.filter(recipient=user).exists()

    def test_notify_users_respects_preferences(self, db):
        """Users with disabled preferences don't receive notifications."""
        users = [UserFactory() for _ in range(3)]
        # Disable notifications for the second user
        users[1].set_notification_preference('system_announcement', 'in_app', False)

        service = NotificationService()
        notifications = service.notify_users(
            users=users,
            notification_type='system_announcement',
            title='System Update',
            message='The system has been updated.',
        )

        assert len(notifications) == 2
        assert not Notification.objects.filter(recipient=users[1]).exists()

    def test_notify_users_with_owner(self, site, notification_settings):
        """Owner user is checked against notify_content_owner setting."""
        notification_settings.notify_content_owner = False
        notification_settings.save()

        owner = UserFactory()
        other_user = UserFactory()
        service = NotificationService(site=site)

        notifications = service.notify_users(
            users=[owner, other_user],
            notification_type='hackathon_created',
            title='New Hackathon',
            message='A new hackathon was created.',
            owner_user=owner,
        )

        # Only non-owner should receive notification
        assert len(notifications) == 1
        assert notifications[0].recipient == other_user

    def test_notify_users_empty_list(self, db):
        """Empty user list returns empty notifications."""
        service = NotificationService()

        notifications = service.notify_users(
            users=[],
            notification_type='system_announcement',
            title='System Update',
            message='The system has been updated.',
        )

        assert notifications == []


class TestUserPreferenceMethods:
    """Tests for User model preference methods."""

    def test_get_notification_preference_default_in_app(self, db):
        """Default in_app preference is True."""
        user = UserFactory()
        result = user.get_notification_preference('team_invitation', 'in_app')
        assert result is True

    def test_get_notification_preference_default_email(self, db):
        """Default email preference is False."""
        user = UserFactory()
        result = user.get_notification_preference('team_invitation', 'email')
        assert result is False

    def test_set_notification_preference(self, db):
        """Can set and retrieve notification preference."""
        user = UserFactory()
        user.set_notification_preference('team_invitation', 'email', True)

        result = user.get_notification_preference('team_invitation', 'email')
        assert result is True

    def test_set_notification_preference_multiple_types(self, db):
        """Can set preferences for multiple types."""
        user = UserFactory()
        user.set_notification_preference('team_invitation', 'email', True)
        user.set_notification_preference('comment_reply', 'in_app', False)

        assert user.get_notification_preference('team_invitation', 'email') is True
        assert user.get_notification_preference('comment_reply', 'in_app') is False
        # Other types unchanged
        assert user.get_notification_preference('system_announcement', 'in_app') is True

    def test_set_notification_preference_persists(self, db):
        """Preferences persist after refresh from DB."""
        user = UserFactory()
        user.set_notification_preference('team_invitation', 'email', True)

        # Refresh from DB
        user.refresh_from_db()

        result = user.get_notification_preference('team_invitation', 'email')
        assert result is True

    def test_get_notification_preference_global_fallback(self, db):
        """Falls back to global channel preference."""
        user = UserFactory()
        user.notification_preferences = {
            'in_app': True,
            'email': True,  # Global email enabled
            'types': {}
        }
        user.save()

        # No type-specific setting, should fall back to global
        result = user.get_notification_preference('team_invitation', 'email')
        assert result is True


class TestNotificationSettingsModel:
    """Tests for NotificationSettings model."""

    def test_is_type_enabled_default(self, site, notification_settings):
        """Types are enabled by default."""
        result = notification_settings.is_type_enabled('team_invitation')
        assert result is True

    def test_is_type_enabled_explicit_true(self, site, notification_settings):
        """Explicitly enabled types return True."""
        notification_settings.enabled_types = {'team_invitation': True}
        notification_settings.save()

        result = notification_settings.is_type_enabled('team_invitation')
        assert result is True

    def test_is_type_enabled_explicit_false(self, site, notification_settings):
        """Explicitly disabled types return False."""
        notification_settings.enabled_types = {'team_invitation': False}
        notification_settings.save()

        result = notification_settings.is_type_enabled('team_invitation')
        assert result is False

    def test_get_default_preferences(self, site, notification_settings):
        """get_default_preferences returns proper structure."""
        notification_settings.default_in_app = True
        notification_settings.default_email = False
        notification_settings.save()

        defaults = notification_settings.get_default_preferences()

        assert defaults['in_app'] is True
        assert defaults['email'] is False
        assert 'types' in defaults
        assert 'team_invitation' in defaults['types']
