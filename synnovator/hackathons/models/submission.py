from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from wagtail.admin.panels import FieldPanel


class Submission(models.Model):
    """
    Represents submissions for quests or hackathon finals.
    Supports file uploads and public repository URLs.
    Manual verification workflow via Wagtail admin.
    """

    # Who submitted (one of these will be set)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='submissions',
        help_text="Individual submitter (for quests)"
    )

    team = models.ForeignKey(
        'Team',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='submissions',
        help_text="Team submitter (for hackathon finals)"
    )

    # What was submitted to (one of these will be set)
    quest = models.ForeignKey(
        'Quest',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='submissions',
        help_text="Quest being attempted"
    )

    hackathon = models.ForeignKey(
        'HackathonPage',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='final_submissions',
        help_text="Hackathon final submission"
    )

    # Submission content
    submission_file = models.FileField(
        upload_to='submissions/%Y/%m/',
        blank=True,
        null=True,
        help_text="Upload submission file (code, document, etc.)"
    )

    submission_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Public repository or demo URL (optional)"
    )

    description = models.TextField(
        blank=True,
        help_text="Submission description and notes"
    )

    # Verification status
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Review'),
            ('verified', 'Verified'),
            ('rejected', 'Rejected'),
        ],
        default='pending'
    )

    # Scoring (manual entry by COO/judges)
    score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Score (0-100) entered by reviewer"
    )

    # Feedback
    feedback = models.TextField(
        blank=True,
        help_text="Reviewer feedback and comments"
    )

    # Metadata
    submitted_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When verification was completed"
    )

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='verified_submissions',
        help_text="Staff member who verified"
    )

    attempt_number = models.PositiveIntegerField(
        default=1,
        help_text="Submission attempt count"
    )

    # P2: Copyright and Originality Checking
    copyright_declaration = models.BooleanField(
        default=False,
        help_text="User confirms ownership or proper licensing of submitted content"
    )

    copyright_notes = models.TextField(
        blank=True,
        help_text="Additional copyright information or licensing details"
    )

    originality_check_status = models.CharField(
        max_length=20,
        choices=[
            ('not_checked', 'Not Checked'),
            ('checking', 'Checking'),
            ('pass', 'Passed'),
            ('warning', 'Warning - Similarity Detected'),
            ('fail', 'Failed - Plagiarism Detected'),
        ],
        default='not_checked',
        help_text="Automated originality verification status"
    )

    originality_check_result = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detailed originality check results (similarity score, sources)"
    )

    file_transfer_confirmed = models.BooleanField(
        default=False,
        help_text="User confirmed file upload completed successfully"
    )

    panels = [
        FieldPanel('verification_status'),
        FieldPanel('score'),
        FieldPanel('feedback'),
        FieldPanel('copyright_declaration'),
        FieldPanel('copyright_notes'),
        FieldPanel('originality_check_status'),
    ]

    class Meta:
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['verification_status']),
            models.Index(fields=['user', '-submitted_at']),
            models.Index(fields=['team', '-submitted_at']),
        ]

    def __str__(self):
        submitter = self.team.name if self.team else (self.user.get_full_name() if self.user else "Unknown")
        target = self.quest.title if self.quest else (self.hackathon.title if self.hackathon else "Unknown")
        return f"Submission by {submitter} for {target}"

    def clean(self):
        # Ensure exactly one submitter
        if not ((self.user and not self.team) or (self.team and not self.user)):
            raise ValidationError("Submission must have either a user OR a team, not both.")
        # Ensure exactly one target
        if not ((self.quest and not self.hackathon) or (self.hackathon and not self.quest)):
            raise ValidationError("Submission must be for either a quest OR a hackathon, not both.")
        # Ensure at least one submission method
        if not self.submission_file and not self.submission_url:
            raise ValidationError("Submission must include a file OR a URL.")
