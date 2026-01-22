"""
Notification service for centralized notification creation and preference checking.

Provides a clean interface for creating notifications while respecting:
- Site-wide settings (NotificationSettings)
- User preferences (User.notification_preferences)
"""
from django.utils.translation import gettext_lazy as _
from wagtail.models import Site


class NotificationService:
    """
    Service for creating notifications with preference checking.

    Usage:
        service = NotificationService()
        service.create_notification(
            recipient=user,
            notification_type='team_invitation',
            title='Team Invitation',
            message='You have been invited to join Team X',
        )
    """

    def __init__(self, site=None):
        """
        Initialize service with optional site.

        Args:
            site: Wagtail Site instance. If None, uses default site.
        """
        self._site = site
        self._settings = None

    @property
    def site(self):
        """Get site, lazily fetching default if not set."""
        if self._site is None:
            self._site = Site.objects.filter(is_default_site=True).first()
        return self._site

    @property
    def settings(self):
        """Get NotificationSettings for the site, lazily loading."""
        if self._settings is None:
            from synnovator.notifications.models import NotificationSettings
            if self.site:
                self._settings = NotificationSettings.for_site(self.site)
            else:
                self._settings = NotificationSettings()
        return self._settings

    def should_notify(
        self,
        user,
        notification_type: str,
        channel: str = 'in_app',
        is_content_owner: bool = False
    ) -> bool:
        """
        Check if a notification should be sent.

        Checks:
        1. Global type enablement
        2. Content owner policy
        3. User preferences

        Args:
            user: User to potentially notify
            notification_type: Type of notification (e.g., 'team_invitation')
            channel: Delivery channel ('in_app' or 'email')
            is_content_owner: Whether user is the owner of the content triggering notification

        Returns:
            True if notification should be sent, False otherwise
        """
        # Check global type enablement
        if not self.settings.is_type_enabled(notification_type):
            return False

        # Check content owner policy
        if is_content_owner and not self.settings.notify_content_owner:
            return False

        # Check user preferences
        return user.get_notification_preference(notification_type, channel)

    def create_notification(
        self,
        recipient,
        notification_type: str,
        title: str,
        message: str,
        link_url: str = '',
        metadata: dict = None,
        is_content_owner: bool = False
    ):
        """
        Create a notification if preferences allow.

        Args:
            recipient: User to receive notification
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            link_url: Optional URL to related content
            metadata: Optional metadata dict
            is_content_owner: Whether recipient is the content owner

        Returns:
            Notification instance if created, None if preferences prevent it
        """
        if not self.should_notify(recipient, notification_type, 'in_app', is_content_owner):
            return None

        from synnovator.notifications.models import Notification

        return Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            link_url=link_url,
            metadata=metadata or {},
        )

    def notify_users(
        self,
        users,
        notification_type: str,
        title: str,
        message: str,
        link_url: str = '',
        metadata: dict = None,
        owner_user=None
    ):
        """
        Create notifications for multiple users.

        Args:
            users: Iterable of users to notify
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            link_url: Optional URL to related content
            metadata: Optional metadata dict
            owner_user: Optional user who owns the content (for is_content_owner check)

        Returns:
            List of created Notification instances
        """
        notifications = []
        for user in users:
            is_owner = owner_user and user.id == owner_user.id
            notification = self.create_notification(
                recipient=user,
                notification_type=notification_type,
                title=title,
                message=message,
                link_url=link_url,
                metadata=metadata,
                is_content_owner=is_owner
            )
            if notification:
                notifications.append(notification)
        return notifications
