"""
Advancement and elimination tracking models for hackathon teams.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet


@register_snippet
class AdvancementLog(models.Model):
    """
    Records team advancement or elimination decisions during hackathon phases.
    Provides audit trail for judging decisions.
    """

    team = models.ForeignKey(
        'hackathons.Team',
        on_delete=models.CASCADE,
        related_name='advancement_logs',
        verbose_name=_("Team"),
        help_text=_("Team affected by this decision")
    )

    from_phase = models.ForeignKey(
        'hackathons.Phase',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='advanced_from',
        verbose_name=_("From Phase"),
        help_text=_("Phase team is advancing from")
    )

    to_phase = models.ForeignKey(
        'hackathons.Phase',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='advanced_to',
        verbose_name=_("To Phase"),
        help_text=_("Phase team is advancing to (if advanced)")
    )

    decision = models.CharField(
        max_length=20,
        choices=[
            ('advanced', _('Advanced to Next Round')),
            ('eliminated', _('Eliminated')),
        ],
        verbose_name=_("Decision"),
        help_text=_("Whether team advanced or was eliminated")
    )

    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='advancement_decisions',
        verbose_name=_("Decided By"),
        help_text=_("Staff member who made the decision")
    )

    decided_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Decision Time")
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Reason for decision or additional notes")
    )

    panels = [
        FieldPanel('team'),
        FieldPanel('decision'),
        FieldPanel('from_phase'),
        FieldPanel('to_phase'),
        FieldPanel('notes'),
    ]

    class Meta:
        ordering = ['-decided_at']
        verbose_name = _("Advancement Log")
        verbose_name_plural = _("Advancement Logs")
        indexes = [
            models.Index(fields=['team', '-decided_at']),
            models.Index(fields=['decision']),
        ]

    def __str__(self):
        return f"{self.team.name} - {self.get_decision_display()} ({self.decided_at.strftime('%Y-%m-%d')})"
