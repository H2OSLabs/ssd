"""
Notification system models.
Implements P1 notification features for user engagement and operational alerts.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.snippets.models import register_snippet
from wagtail_localize.models import TranslatableMixin


# Notification type constants - single source of truth
NOTIFICATION_TYPES = [
    ('violation_alert', _('Rule Violation Alert')),
    ('deadline_reminder', _('Deadline Reminder')),
    ('advancement_result', _('Advancement Result')),
    ('submission_reviewed', _('Submission Reviewed')),
    ('team_invitation', _('Team Invitation')),
    ('comment_reply', _('Comment Reply')),
    ('post_liked', _('Post Liked')),
    ('new_follower', _('New Follower')),
    ('system_announcement', _('System Announcement')),
    ('login_success', _('Login Success')),
    ('hackathon_created', _('New Hackathon Created')),
]


@register_setting(icon="bell")
class NotificationSettings(TranslatableMixin, BaseSiteSetting):
    """
    Site-wide notification configuration.

    Admins can control:
    - Which notification types are enabled globally
    - Default channel preferences (in-app, email)
    - Whether content owners receive their own notifications
    """

    enabled_types = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Enabled Notification Types"),
        help_text=_("Format: {'type_key': true/false}")
    )

    default_in_app = models.BooleanField(
        default=True,
        verbose_name=_("Default In-App Notifications"),
        help_text=_("Enable in-app notifications by default")
    )

    default_email = models.BooleanField(
        default=False,
        verbose_name=_("Default Email Notifications"),
        help_text=_("Enable email notifications by default")
    )

    notify_content_owner = models.BooleanField(
        default=True,
        verbose_name=_("Notify Content Owner"),
        help_text=_("Include content creators in notifications about their own content")
    )

    class Meta:
        unique_together = [("translation_key", "locale")]
        verbose_name = _("Notification Settings")
        verbose_name_plural = _("Notification Settings")

    panels = [
        MultiFieldPanel([
            FieldPanel('enabled_types'),
        ], heading=_("Notification Types")),
        MultiFieldPanel([
            FieldPanel('default_in_app'),
            FieldPanel('default_email'),
        ], heading=_("Default Channels")),
        FieldPanel('notify_content_owner'),
    ]

    def is_type_enabled(self, notification_type: str) -> bool:
        """Check if a notification type is enabled globally."""
        return self.enabled_types.get(notification_type, True)

    def get_default_preferences(self) -> dict:
        """Return default preferences structure for new users."""
        return {
            'in_app': self.default_in_app,
            'email': self.default_email,
            'types': {t[0]: True for t in NOTIFICATION_TYPES}
        }


@register_snippet
class Notification(models.Model):
    """
    User notification system for alerts, updates, and reminders.
    Supports various notification types including rule violations, deadlines, and advancement decisions.
    """

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_("Recipient")
    )

    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        verbose_name=_("Notification Type"),
        db_index=True
    )

    title = models.CharField(
        max_length=200,
        verbose_name=_("Title"),
        help_text=_("Notification title")
    )

    message = models.TextField(
        verbose_name=_("Message"),
        help_text=_("Notification content")
    )

    # Optional link to related object
    link_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name=_("Link URL"),
        help_text=_("Optional URL to related content")
    )

    # Metadata as JSON (flexible for different notification types)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadata"),
        help_text=_("Additional data specific to notification type (JSON)")
    )

    # Status tracking
    is_read = models.BooleanField(
        default=False,
        verbose_name=_("Is Read"),
        db_index=True
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Read At")
    )

    # Delivery channels
    sent_email = models.BooleanField(
        default=False,
        verbose_name=_("Sent Email"),
        help_text=_("Whether email notification was sent")
    )

    email_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Email Sent At")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )

    panels = [
        FieldPanel('recipient'),
        FieldPanel('notification_type'),
        FieldPanel('title'),
        FieldPanel('message'),
        FieldPanel('link_url'),
        FieldPanel('metadata'),
        FieldPanel('is_read'),
    ]

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read', '-created_at']),
            models.Index(fields=['notification_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.recipient.username}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    @classmethod
    def create_violation_notification(cls, team, rule_violation):
        """Create notification for rule violation"""
        # Notify team leader
        leader = team.get_leader()
        if leader:
            return cls.objects.create(
                recipient=leader.user,
                notification_type='violation_alert',
                title=_("Rule Violation Detected"),
                message=_("Your team '{}' has violated rule: {}").format(
                    team.name,
                    rule_violation.rule.title
                ),
                link_url=f"/admin/snippets/hackathons/ruleviolation/edit/{rule_violation.id}/",
                metadata={
                    'team_id': team.id,
                    'violation_id': rule_violation.id,
                    'rule_id': rule_violation.rule.id,
                }
            )

    @classmethod
    def create_advancement_notification(cls, team, advancement_log):
        """Create notification for advancement decision"""
        leader = team.get_leader()
        if leader:
            if advancement_log.decision == 'advanced':
                title = _("Congratulations! Your Team Advanced")
                message = _("Your team '{}' has advanced to the next round").format(team.name)
            else:
                title = _("Team Eliminated")
                message = _("Your team '{}' has been eliminated").format(team.name)

            return cls.objects.create(
                recipient=leader.user,
                notification_type='advancement_result',
                title=title,
                message=message,
                link_url=f"/admin/snippets/hackathons/advancementlog/edit/{advancement_log.id}/",
                metadata={
                    'team_id': team.id,
                    'advancement_log_id': advancement_log.id,
                    'decision': advancement_log.decision,
                }
            )
