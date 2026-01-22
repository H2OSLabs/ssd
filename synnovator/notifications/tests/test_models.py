"""
Tests for notifications models.
"""

import pytest
from django.utils import timezone

from synnovator.notifications.tests.factories import (
    NotificationFactory,
    ViolationAlertFactory,
    DeadlineReminderFactory,
    AdvancementResultFactory,
    SubmissionReviewedFactory,
    TeamInvitationFactory,
    CommentReplyFactory,
    PostLikedFactory,
    NewFollowerFactory,
    ReadNotificationFactory,
)
from synnovator.users.tests.factories import UserFactory


class TestNotification:
    """Tests for Notification model."""

    def test_notification_creation(self, db):
        """Notification can be created."""
        notification = NotificationFactory()
        assert notification.pk is not None
        assert notification.recipient is not None
        assert notification.title

    def test_notification_str_representation(self, db):
        """Notification __str__ returns type and recipient."""
        recipient = UserFactory(username="testuser")
        notification = NotificationFactory(
            recipient=recipient,
            notification_type="system_announcement"
        )
        assert "System Announcement" in str(notification)
        assert "testuser" in str(notification)

    def test_notification_default_is_read(self, db):
        """Notification default is_read is False."""
        notification = NotificationFactory()
        assert notification.is_read is False
        assert notification.read_at is None

    def test_notification_type_choices(self, db):
        """Notification accepts valid type choices."""
        types = [
            "violation_alert",
            "deadline_reminder",
            "advancement_result",
            "submission_reviewed",
            "team_invitation",
            "comment_reply",
            "post_liked",
            "new_follower",
            "system_announcement",
        ]
        for notification_type in types:
            notification = NotificationFactory(notification_type=notification_type)
            assert notification.notification_type == notification_type


class TestNotificationTypes:
    """Tests for specific notification types."""

    def test_violation_alert(self, db):
        """Violation alert notification."""
        notification = ViolationAlertFactory()
        assert notification.notification_type == "violation_alert"
        assert "Violation" in notification.title

    def test_deadline_reminder(self, db):
        """Deadline reminder notification."""
        notification = DeadlineReminderFactory()
        assert notification.notification_type == "deadline_reminder"
        assert "Deadline" in notification.title

    def test_advancement_result(self, db):
        """Advancement result notification."""
        notification = AdvancementResultFactory()
        assert notification.notification_type == "advancement_result"
        assert "Advancement" in notification.title

    def test_submission_reviewed(self, db):
        """Submission reviewed notification."""
        notification = SubmissionReviewedFactory()
        assert notification.notification_type == "submission_reviewed"
        assert "Reviewed" in notification.title

    def test_team_invitation(self, db):
        """Team invitation notification."""
        notification = TeamInvitationFactory()
        assert notification.notification_type == "team_invitation"
        assert "Invitation" in notification.title

    def test_comment_reply(self, db):
        """Comment reply notification."""
        notification = CommentReplyFactory()
        assert notification.notification_type == "comment_reply"
        assert "Reply" in notification.title

    def test_post_liked(self, db):
        """Post liked notification."""
        notification = PostLikedFactory()
        assert notification.notification_type == "post_liked"
        assert "Liked" in notification.title

    def test_new_follower(self, db):
        """New follower notification."""
        notification = NewFollowerFactory()
        assert notification.notification_type == "new_follower"
        assert "Follower" in notification.title


class TestNotificationMethods:
    """Tests for Notification methods."""

    def test_mark_as_read(self, db):
        """mark_as_read updates is_read and read_at."""
        notification = NotificationFactory(is_read=False)
        assert notification.is_read is False
        assert notification.read_at is None

        notification.mark_as_read()

        notification.refresh_from_db()
        assert notification.is_read is True
        assert notification.read_at is not None

    def test_mark_as_read_idempotent(self, db):
        """mark_as_read is idempotent."""
        notification = NotificationFactory(is_read=False)
        notification.mark_as_read()
        first_read_at = notification.read_at

        # Call again
        notification.mark_as_read()

        # Should not update read_at
        notification.refresh_from_db()
        assert notification.read_at == first_read_at

    def test_already_read_notification(self, db):
        """Already read notification stays read."""
        notification = ReadNotificationFactory()
        assert notification.is_read is True
        assert notification.read_at is not None


class TestNotificationMetadata:
    """Tests for Notification metadata field."""

    def test_notification_with_metadata(self, db):
        """Notification can have metadata."""
        notification = NotificationFactory(
            metadata={
                "team_id": 1,
                "hackathon_id": 2,
                "custom_field": "value",
            }
        )
        assert notification.metadata["team_id"] == 1
        assert notification.metadata["hackathon_id"] == 2
        assert notification.metadata["custom_field"] == "value"

    def test_notification_default_empty_metadata(self, db):
        """Notification has empty dict as default metadata."""
        notification = NotificationFactory()
        assert notification.metadata == {}

    def test_notification_link_url(self, db):
        """Notification can have link URL."""
        notification = NotificationFactory(
            link_url="https://example.com/page/123/"
        )
        assert notification.link_url == "https://example.com/page/123/"


class TestNotificationEmail:
    """Tests for Notification email tracking."""

    def test_notification_default_not_sent(self, db):
        """Notification email not sent by default."""
        notification = NotificationFactory()
        assert notification.sent_email is False
        assert notification.email_sent_at is None

    def test_notification_mark_email_sent(self, db):
        """Notification can track email sent."""
        notification = NotificationFactory()
        notification.sent_email = True
        notification.email_sent_at = timezone.now()
        notification.save()

        notification.refresh_from_db()
        assert notification.sent_email is True
        assert notification.email_sent_at is not None


class TestNotificationQueries:
    """Tests for common notification queries."""

    def test_unread_notifications(self, db):
        """Can filter unread notifications."""
        from synnovator.notifications.models import Notification

        user = UserFactory()
        NotificationFactory(recipient=user, is_read=False)
        NotificationFactory(recipient=user, is_read=False)
        NotificationFactory(recipient=user, is_read=True)

        unread = Notification.objects.filter(recipient=user, is_read=False)
        assert unread.count() == 2

    def test_notifications_by_type(self, db):
        """Can filter notifications by type."""
        from synnovator.notifications.models import Notification

        user = UserFactory()
        ViolationAlertFactory(recipient=user)
        ViolationAlertFactory(recipient=user)
        DeadlineReminderFactory(recipient=user)

        violations = Notification.objects.filter(
            recipient=user,
            notification_type="violation_alert"
        )
        assert violations.count() == 2

    def test_notifications_ordered_by_created_at(self, db):
        """Notifications are ordered by created_at descending."""
        from synnovator.notifications.models import Notification

        user = UserFactory()
        old = NotificationFactory(recipient=user, title="Old")
        new = NotificationFactory(recipient=user, title="New")

        notifications = list(Notification.objects.filter(recipient=user))
        assert notifications[0] == new  # Newest first
        assert notifications[1] == old
