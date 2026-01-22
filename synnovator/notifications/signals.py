"""
Signal handlers for notification triggers.

Handles:
- user_logged_in: Creates login success notification
- page_published: Creates hackathon created notification for admins
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from wagtail.signals import page_published

from synnovator.notifications.services import NotificationService

User = get_user_model()


@receiver(user_logged_in)
def notify_on_login(sender, request, user, **kwargs):
    """
    Create a login success notification when user logs in.
    Uses NotificationService to respect user preferences.
    """
    service = NotificationService()
    notification = service.create_notification(
        recipient=user,
        notification_type='login_success',
        title=str(_("Login Successful")),
        message=str(_("You have successfully logged in.")),
        is_content_owner=True,  # User is the "owner" of their own login
    )
    # If notification was created, mark as read since user just logged in
    if notification:
        notification.is_read = True
        notification.save(update_fields=['is_read'])


@receiver(page_published)
def notify_admins_on_hackathon_created(sender, instance, **kwargs):
    """
    Notify admin users when a new HackathonPage is published for the first time.

    Only triggers on first publish (when first_published_at was just set).
    Uses NotificationService to respect preferences.
    """
    from django.utils import timezone
    from synnovator.hackathons.models import HackathonPage

    # Only handle HackathonPage
    if not isinstance(instance, HackathonPage):
        return

    # Check if first_published_at is set
    if instance.first_published_at is None:
        return

    # Check if this is the first publish by verifying first_published_at
    # was set recently (within the last 60 seconds)
    time_since_first_publish = (timezone.now() - instance.first_published_at).total_seconds()
    if time_since_first_publish > 60:
        return  # Was published more than a minute ago, not first publish

    # Get all superusers (admins)
    admins = User.objects.filter(is_superuser=True)

    creator_name = instance.owner.username if instance.owner else str(_("Someone"))

    # Use NotificationService to handle preferences
    service = NotificationService()
    service.notify_users(
        users=admins,
        notification_type='hackathon_created',
        title=str(_("New Hackathon Created")),
        message=str(_("{username} created a new hackathon: {title}")).format(
            username=creator_name,
            title=instance.title
        ),
        link_url=instance.get_url() or '',
        metadata={
            'hackathon_id': instance.id,
            'hackathon_title': instance.title,
            'created_by': instance.owner.username if instance.owner else None,
        },
        owner_user=instance.owner,  # Owner will be checked against notify_content_owner
    )
