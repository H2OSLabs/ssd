"""
Factory Boy factories for notifications app.
"""

import factory
from factory.django import DjangoModelFactory

from synnovator.notifications.models import Notification
from synnovator.users.tests.factories import UserFactory


class NotificationFactory(DjangoModelFactory):
    """Factory for Notification."""

    class Meta:
        model = Notification

    recipient = factory.SubFactory(UserFactory)
    notification_type = "system_announcement"
    title = factory.Sequence(lambda n: f"Notification {n}")
    message = factory.Faker("sentence")
    link_url = ""
    metadata = factory.LazyFunction(lambda: {})
    is_read = False
    sent_email = False


class ViolationAlertFactory(NotificationFactory):
    """Factory for violation alert notifications."""

    notification_type = "violation_alert"
    title = "Rule Violation Detected"


class DeadlineReminderFactory(NotificationFactory):
    """Factory for deadline reminder notifications."""

    notification_type = "deadline_reminder"
    title = "Deadline Approaching"


class AdvancementResultFactory(NotificationFactory):
    """Factory for advancement result notifications."""

    notification_type = "advancement_result"
    title = "Advancement Result"


class SubmissionReviewedFactory(NotificationFactory):
    """Factory for submission reviewed notifications."""

    notification_type = "submission_reviewed"
    title = "Submission Reviewed"


class TeamInvitationFactory(NotificationFactory):
    """Factory for team invitation notifications."""

    notification_type = "team_invitation"
    title = "Team Invitation"


class CommentReplyFactory(NotificationFactory):
    """Factory for comment reply notifications."""

    notification_type = "comment_reply"
    title = "New Reply to Your Comment"


class PostLikedFactory(NotificationFactory):
    """Factory for post liked notifications."""

    notification_type = "post_liked"
    title = "Your Post Was Liked"


class NewFollowerFactory(NotificationFactory):
    """Factory for new follower notifications."""

    notification_type = "new_follower"
    title = "New Follower"


class ReadNotificationFactory(NotificationFactory):
    """Factory for read notifications."""

    is_read = True
    read_at = factory.LazyFunction(lambda: __import__("django.utils.timezone", fromlist=["now"]).now())
