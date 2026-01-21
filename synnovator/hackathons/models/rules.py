"""
Competition rule definition and violation tracking models.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from modelcluster.fields import ParentalKey


class CompetitionRule(models.Model):
    """
    Defines rules and constraints for hackathon competitions.
    Can be used to automatically check team compliance.
    """

    hackathon = ParentalKey(
        'hackathons.HackathonPage',
        on_delete=models.CASCADE,
        related_name='rules',
        verbose_name=_("Hackathon")
    )

    rule_type = models.CharField(
        max_length=50,
        choices=[
            ('team_size', _('Team Size')),
            ('team_composition', _('Team Composition')),
            ('submission_format', _('Submission Format')),
            ('eligibility', _('Participant Eligibility')),
            ('conduct', _('Code of Conduct')),
            ('deadline', _('Deadline')),
            ('other', _('Other')),
        ],
        verbose_name=_("Rule Type"),
        help_text=_("Category of this rule")
    )

    title = models.CharField(
        max_length=200,
        verbose_name=_("Title"),
        help_text=_("Short title for this rule")
    )

    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Detailed description of the rule")
    )

    rule_definition = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Rule Definition"),
        help_text=_("Rule configuration as JSON (e.g., {'min_members': 2, 'max_members': 5})")
    )

    is_mandatory = models.BooleanField(
        default=True,
        verbose_name=_("Is Mandatory"),
        help_text=_("Whether violation leads to disqualification")
    )

    penalty = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('warning', _('Warning')),
            ('point_deduction', _('Point Deduction')),
            ('disqualification', _('Disqualification')),
        ],
        verbose_name=_("Penalty"),
        help_text=_("Consequence of violation")
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Display Order"),
        help_text=_("Order in which rules are displayed")
    )

    panels = [
        FieldPanel('rule_type'),
        FieldPanel('title'),
        FieldPanel('description'),
        FieldPanel('rule_definition'),
        FieldPanel('is_mandatory'),
        FieldPanel('penalty'),
        FieldPanel('order'),
    ]

    class Meta:
        ordering = ['order', 'id']
        verbose_name = _("Competition Rule")
        verbose_name_plural = _("Competition Rules")

    def __str__(self):
        return f"{self.title} ({self.get_rule_type_display()})"

    def check_compliance(self, team):
        """
        Check if a team complies with this rule.
        Returns (is_compliant: bool, message: str)
        """
        if self.rule_type == 'team_size':
            min_size = self.rule_definition.get('min_members', 0)
            max_size = self.rule_definition.get('max_members', 999)
            member_count = team.members.count()

            if member_count < min_size:
                return False, f"Team has {member_count} members, minimum is {min_size}"
            if member_count > max_size:
                return False, f"Team has {member_count} members, maximum is {max_size}"
            return True, "Team size compliant"

        elif self.rule_type == 'team_composition':
            required_roles = self.rule_definition.get('required_roles', [])
            current_roles = set(team.membership.values_list('role', flat=True))

            missing_roles = set(required_roles) - current_roles
            if missing_roles:
                return False, f"Missing required roles: {', '.join(missing_roles)}"
            return True, "Team composition compliant"

        elif self.rule_type == 'submission_format':
            # Check if team has submitted required files
            has_submission = team.submissions.filter(
                verification_status__in=['verified', 'pending']
            ).exists()

            if not has_submission:
                return False, "No valid submission found"
            return True, "Submission format compliant"

        # Default for other rule types
        return True, "Manual verification required"


@register_snippet
class RuleViolation(models.Model):
    """
    Records violations of competition rules by teams.
    Can be detected automatically or reported manually.
    """

    team = models.ForeignKey(
        'hackathons.Team',
        on_delete=models.CASCADE,
        related_name='violations',
        verbose_name=_("Team")
    )

    rule = models.ForeignKey(
        CompetitionRule,
        on_delete=models.CASCADE,
        verbose_name=_("Rule"),
        help_text=_("Rule that was violated")
    )

    detected_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Detected At")
    )

    detection_method = models.CharField(
        max_length=20,
        choices=[
            ('automated', _('Automated Check')),
            ('manual', _('Manual Report')),
        ],
        verbose_name=_("Detection Method")
    )

    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Details of the violation")
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', _('Pending Review')),
            ('confirmed', _('Confirmed')),
            ('dismissed', _('Dismissed')),
        ],
        default='pending',
        verbose_name=_("Status")
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Reviewed By"),
        help_text=_("Staff member who reviewed this violation")
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Reviewed At")
    )

    action_taken = models.TextField(
        blank=True,
        verbose_name=_("Action Taken"),
        help_text=_("What action was taken in response to this violation")
    )

    panels = [
        FieldPanel('team'),
        FieldPanel('rule'),
        FieldPanel('detection_method'),
        FieldPanel('description'),
        FieldPanel('status'),
        FieldPanel('action_taken'),
    ]

    class Meta:
        ordering = ['-detected_at']
        verbose_name = _("Rule Violation")
        verbose_name_plural = _("Rule Violations")
        indexes = [
            models.Index(fields=['team', '-detected_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.team.name} - {self.rule.title} ({self.get_status_display()})"
