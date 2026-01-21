"""
Multi-judge scoring system models.
Implements P1 requirement for multi-dimensional evaluation with multiple judges.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet


@register_snippet
class JudgeScore(models.Model):
    """
    Individual judge's scores for a team submission.
    Supports multi-dimensional evaluation (technical, commercial, operational).
    """

    submission = models.ForeignKey(
        'hackathons.Submission',
        on_delete=models.CASCADE,
        related_name='judge_scores',
        verbose_name=_("Submission")
    )

    judge = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='judge_scores_given',
        verbose_name=_("Judge"),
        help_text=_("Staff member who provided this score")
    )

    # Multi-dimensional scoring
    technical_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.0,
        verbose_name=_("Technical Score"),
        help_text=_("Score for technical implementation (0-100)")
    )

    commercial_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.0,
        verbose_name=_("Commercial Score"),
        help_text=_("Score for business viability (0-100)")
    )

    operational_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.0,
        verbose_name=_("Operational Score"),
        help_text=_("Score for operational feasibility (0-100)")
    )

    overall_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.0,
        verbose_name=_("Overall Score"),
        help_text=_("Overall score (calculated or manual)")
    )

    # Detailed feedback
    feedback = models.TextField(
        blank=True,
        verbose_name=_("Feedback"),
        help_text=_("Detailed feedback from judge")
    )

    # Scoring breakdown (optional detailed criteria)
    score_breakdown = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Score Breakdown"),
        help_text=_("Detailed scoring criteria as JSON")
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )

    panels = [
        FieldPanel('submission'),
        FieldPanel('judge'),
        FieldPanel('technical_score'),
        FieldPanel('commercial_score'),
        FieldPanel('operational_score'),
        FieldPanel('overall_score'),
        FieldPanel('feedback'),
        FieldPanel('score_breakdown'),
    ]

    class Meta:
        unique_together = [['submission', 'judge']]
        ordering = ['-created_at']
        verbose_name = _("Judge Score")
        verbose_name_plural = _("Judge Scores")
        indexes = [
            models.Index(fields=['submission', '-created_at']),
            models.Index(fields=['judge', '-created_at']),
        ]

    def __str__(self):
        return f"{self.judge.username}'s score for submission {self.submission.id}"

    def save(self, *args, **kwargs):
        """Calculate overall score if not set"""
        if self.overall_score == 0.0:
            self.overall_score = (
                self.technical_score + self.commercial_score + self.operational_score
            ) / 3
        super().save(*args, **kwargs)

        # Update team's aggregated scores
        if self.submission.team:
            self.submission.team.update_scores()


class ScoreBreakdown(models.Model):
    """
    Detailed scoring criteria breakdown.
    Allows defining custom scoring criteria for different hackathon types.
    """

    hackathon = models.ForeignKey(
        'hackathons.HackathonPage',
        on_delete=models.CASCADE,
        related_name='scoring_criteria',
        verbose_name=_("Hackathon")
    )

    category = models.CharField(
        max_length=50,
        choices=[
            ('technical', _('Technical')),
            ('commercial', _('Commercial')),
            ('operational', _('Operational')),
        ],
        verbose_name=_("Category")
    )

    criterion_name = models.CharField(
        max_length=200,
        verbose_name=_("Criterion Name"),
        help_text=_("e.g., 'Code Quality', 'Market Fit', 'Scalability'")
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("What this criterion evaluates")
    )

    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.0,
        verbose_name=_("Weight"),
        help_text=_("Weight in final score calculation")
    )

    max_points = models.PositiveIntegerField(
        default=100,
        verbose_name=_("Maximum Points"),
        help_text=_("Maximum points for this criterion")
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Display Order")
    )

    class Meta:
        ordering = ['hackathon', 'category', 'order']
        verbose_name = _("Score Breakdown Criterion")
        verbose_name_plural = _("Score Breakdown Criteria")
        indexes = [
            models.Index(fields=['hackathon', 'category']),
        ]

    def __str__(self):
        return f"{self.criterion_name} ({self.get_category_display()}) - {self.hackathon.title}"
