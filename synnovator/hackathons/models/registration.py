"""
Hackathon registration tracking models.
Implements P1 requirement for managing participant registration.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet


@register_snippet
class HackathonRegistration(models.Model):
    """
    Tracks individual user registrations for hackathons.
    Separate from Team model to support registration before team formation.
    """

    hackathon = models.ForeignKey(
        'hackathons.HackathonPage',
        on_delete=models.CASCADE,
        related_name='registrations',
        verbose_name=_("Hackathon")
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hackathon_registrations',
        verbose_name=_("User")
    )

    # Registration status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', _('Pending Approval')),
            ('approved', _('Approved')),
            ('rejected', _('Rejected')),
            ('withdrawn', _('Withdrawn')),
        ],
        default='approved',
        verbose_name=_("Status"),
        db_index=True
    )

    # User preferences
    preferred_role = models.CharField(
        max_length=50,
        choices=[
            ('hacker', _('Hacker (Engineer)')),
            ('hipster', _('Hipster (Designer/UX)')),
            ('hustler', _('Hustler (Business/Marketing)')),
            ('any', _('Any Role')),
        ],
        default='any',
        verbose_name=_("Preferred Role"),
        help_text=_("Role preference for team formation")
    )

    is_seeking_team = models.BooleanField(
        default=True,
        verbose_name=_("Seeking Team"),
        help_text=_("Show in team formation page")
    )

    # Application details
    motivation = models.TextField(
        blank=True,
        verbose_name=_("Motivation"),
        help_text=_("Why user wants to participate")
    )

    skills = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Skills"),
        help_text=_("User's skills for team matching")
    )

    # Team assignment (optional)
    team = models.ForeignKey(
        'hackathons.Team',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='registrations',
        verbose_name=_("Team"),
        help_text=_("Team user joined (if any)")
    )

    # Review fields (for hackathons requiring approval)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='registrations_reviewed',
        verbose_name=_("Reviewed By")
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Reviewed At")
    )

    rejection_reason = models.TextField(
        blank=True,
        verbose_name=_("Rejection Reason"),
        help_text=_("Reason for rejection (if applicable)")
    )

    # Timestamps
    registered_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Registered At")
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )

    panels = [
        FieldPanel('hackathon'),
        FieldPanel('user'),
        FieldPanel('status'),
        FieldPanel('preferred_role'),
        FieldPanel('is_seeking_team'),
        FieldPanel('motivation'),
        FieldPanel('skills'),
        FieldPanel('team'),
        FieldPanel('rejection_reason'),
    ]

    class Meta:
        unique_together = [['hackathon', 'user']]
        ordering = ['-registered_at']
        verbose_name = _("Hackathon Registration")
        verbose_name_plural = _("Hackathon Registrations")
        indexes = [
            models.Index(fields=['hackathon', 'status', '-registered_at']),
            models.Index(fields=['user', '-registered_at']),
            models.Index(fields=['hackathon', 'is_seeking_team', 'status']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.hackathon.title} ({self.get_status_display()})"

    def approve(self, reviewer):
        """Approve registration"""
        from django.utils import timezone
        self.status = 'approved'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()

    def reject(self, reviewer, reason=""):
        """Reject registration"""
        from django.utils import timezone
        self.status = 'rejected'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save()
