from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page
from wagtail.search import index
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.documents.blocks import DocumentChooserBlock
from modelcluster.fields import ParentalKey

from synnovator.utils.models import BasePage


# Status choices for SubmissionPage - defined at module level for reuse
SUBMISSION_STATUS_CHOICES = [
    ('draft', _('Draft')),
    ('submitted', _('Submitted')),
    ('under_review', _('Under Review')),
    ('verified', _('Verified')),
    ('rejected', _('Rejected')),
    ('needs_revision', _('Needs Revision')),
]


class Submission(models.Model):
    """
    Represents submissions for quests or hackathon finals.
    Supports file uploads and public repository URLs.
    Manual verification workflow via Wagtail admin.
    
    Submission types:
    - Quest submission: user + quest (quests are part of hackathon phases)
    - Hackathon submission: team + hackathon (final project submission)
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


# =============================================================================
# SubmissionPage - Wagtail Page for Hackathon Project Submissions
# =============================================================================


class SubmissionPage(BasePage):
    """
    Project submission page for hackathons.

    This is a Wagtail Page that:
    - Lives as a child of SubmissionIndexPage
    - Can be associated with multiple HackathonPages (many-to-many)
    - Links to either a TeamProfilePage or an individual User
    - Uses StreamField for flexible content (documents, images, videos, GitHub links)

    Usage:
    - Submitting to a hackathon = Creating a SubmissionPage and associating it with HackathonPage(s)
    - The many-to-many relationship allows one submission to participate in multiple hackathons
    """

    # Many-to-many relationship with hackathons
    hackathons = models.ManyToManyField(
        'hackathons.HackathonPage',
        related_name='submissions',
        blank=True,
        verbose_name=_("Hackathons"),
        help_text=_("Hackathons this submission participates in")
    )

    # Submitter - either a team or an individual (one must be set)
    team_profile = models.ForeignKey(
        'community.TeamProfilePage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='submissions',
        verbose_name=_("Team"),
        help_text=_("The team submitting this project (leave empty for individual submission)")
    )

    submitter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='submission_pages',
        verbose_name=_("Submitter"),
        help_text=_("Individual user submitting this project (leave empty for team submission)")
    )

    # Project information
    tagline = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Tagline"),
        help_text=_("Short project description (one-liner)")
    )

    # Main content using StreamField for extensibility
    content = StreamField([
        ('heading', blocks.CharBlock(
            form_classname="title",
            help_text=_("Section heading")
        )),
        ('paragraph', blocks.RichTextBlock(
            help_text=_("Rich text content")
        )),
        ('document', DocumentChooserBlock(
            help_text=_("Upload a document (PDF, Markdown, etc.)")
        )),
        ('image', ImageChooserBlock(
            help_text=_("Upload an image")
        )),
        ('video_url', blocks.URLBlock(
            help_text=_("Video URL (YouTube, Vimeo, etc.)")
        )),
        ('github_repo', blocks.StructBlock([
            ('url', blocks.URLBlock(label=_("Repository URL"))),
            ('description', blocks.CharBlock(required=False, label=_("Description"))),
            ('branch', blocks.CharBlock(required=False, default="main", label=_("Branch"))),
        ], help_text=_("GitHub repository link"))),
        ('demo_url', blocks.URLBlock(
            help_text=_("Live demo URL")
        )),
        ('code_block', blocks.StructBlock([
            ('language', blocks.ChoiceBlock(choices=[
                ('python', 'Python'),
                ('javascript', 'JavaScript'),
                ('typescript', 'TypeScript'),
                ('go', 'Go'),
                ('rust', 'Rust'),
                ('other', 'Other'),
            ], default='python')),
            ('code', blocks.TextBlock()),
        ], help_text=_("Code snippet"))),
    ], blank=True, use_json_field=True, verbose_name=_("Content"))

    # Verification and scoring
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ('draft', _('Draft')),
            ('submitted', _('Submitted')),
            ('under_review', _('Under Review')),
            ('verified', _('Verified')),
            ('rejected', _('Rejected')),
            ('needs_revision', _('Needs Revision')),
        ],
        default='draft',
        verbose_name=_("Status")
    )

    score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Score"),
        help_text=_("Score (0-100) entered by reviewer")
    )

    feedback = models.TextField(
        blank=True,
        verbose_name=_("Feedback"),
        help_text=_("Reviewer feedback and comments")
    )

    # Verification metadata
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Submitted At")
    )

    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Verified At")
    )

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='verified_submission_pages',
        verbose_name=_("Verified By")
    )

    # Page configuration - now under SubmissionIndexPage instead of HackathonPage
    parent_page_types = ['hackathons.SubmissionIndexPage']
    subpage_types = []

    content_panels = BasePage.content_panels + [
        FieldPanel('hackathons'),
        MultiFieldPanel([
            FieldPanel('team_profile'),
            FieldPanel('submitter'),
        ], heading=_("Submitter")),
        FieldPanel('tagline'),
        FieldPanel('content'),
        MultiFieldPanel([
            FieldPanel('verification_status'),
            FieldPanel('score'),
            FieldPanel('feedback'),
        ], heading=_("Review")),
    ]

    search_fields = BasePage.search_fields + [
        index.SearchField('tagline'),
        index.FilterField('verification_status'),
    ]

    class Meta:
        verbose_name = _("Project Submission")
        verbose_name_plural = _("Project Submissions")
        indexes = [
            models.Index(fields=['verification_status']),
        ]

    def clean(self):
        """Validate that either team_profile or submitter is set, but not both"""
        super().clean()
        if self.team_profile and self.submitter:
            raise ValidationError(
                _("A submission must have either a team OR an individual submitter, not both.")
            )
        if not self.team_profile and not self.submitter:
            raise ValidationError(
                _("A submission must have either a team or an individual submitter.")
            )

    def get_hackathons(self):
        """Get all associated hackathons"""
        return self.hackathons.all()

    def get_primary_hackathon(self):
        """Get the first associated hackathon (for backward compatibility)"""
        return self.hackathons.first()

    def submit(self):
        """Mark submission as submitted"""
        from django.utils import timezone
        self.verification_status = 'submitted'
        self.submitted_at = timezone.now()
        self.save()

    def verify(self, reviewer, score=None, feedback=""):
        """Verify the submission"""
        from django.utils import timezone
        self.verification_status = 'verified'
        self.verified_at = timezone.now()
        self.verified_by = reviewer
        if score is not None:
            self.score = score
        if feedback:
            self.feedback = feedback
        self.save()

    def reject(self, reviewer, feedback=""):
        """Reject the submission"""
        from django.utils import timezone
        self.verification_status = 'rejected'
        self.verified_at = timezone.now()
        self.verified_by = reviewer
        if feedback:
            self.feedback = feedback
        self.save()

    def user_can_edit(self, user):
        """Check if user can edit this submission"""
        if not user.is_authenticated:
            return False
        # Individual submitter can edit
        if self.submitter and self.submitter == user:
            return True
        # Team members can edit
        if self.team_profile and self.team_profile.is_member(user):
            return True
        # Superusers can edit
        return user.is_superuser

    def get_submitter_display(self):
        """Get display name for the submitter"""
        if self.team_profile:
            return self.team_profile.title
        elif self.submitter:
            return self.submitter.get_full_name() or self.submitter.username
        return _("Unknown")


# =============================================================================
# SubmissionIndexPage - Listing page for submissions with configurable filters
# =============================================================================


class SubmissionIndexPage(BasePage):
    """
    Submission listing page with admin-configurable filters.

    This is the index page for all submissions on the platform.
    Administrators can configure which filters are enabled and set default values.
    """

    intro = RichTextField(
        blank=True,
        verbose_name=_("Introduction"),
        help_text=_("Introduction text displayed at the top of the submissions listing page")
    )

    # Filter toggles (admin configurable)
    enable_hackathon_filter = models.BooleanField(
        default=True,
        verbose_name=_("Enable hackathon filter")
    )
    enable_date_filter = models.BooleanField(
        default=True,
        verbose_name=_("Enable date range filter")
    )
    enable_submitter_filter = models.BooleanField(
        default=True,
        verbose_name=_("Enable submitter filter")
    )
    enable_team_filter = models.BooleanField(
        default=True,
        verbose_name=_("Enable team filter")
    )
    enable_status_filter = models.BooleanField(
        default=True,
        verbose_name=_("Enable status filter")
    )

    # Default filter values (optional)
    default_hackathon = models.ForeignKey(
        'hackathons.HackathonPage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Default hackathon filter"),
        help_text=_("Pre-select a hackathon when page loads")
    )
    default_status = models.CharField(
        max_length=20,
        blank=True,
        choices=SUBMISSION_STATUS_CHOICES,
        verbose_name=_("Default status filter")
    )

    # Page configuration
    parent_page_types = ['home.HomePage']
    subpage_types = ['hackathons.SubmissionPage']
    max_count = 1  # Only one instance allowed

    content_panels = BasePage.content_panels + [
        FieldPanel('intro'),
        MultiFieldPanel([
            FieldPanel('enable_hackathon_filter'),
            FieldPanel('enable_date_filter'),
            FieldPanel('enable_submitter_filter'),
            FieldPanel('enable_team_filter'),
            FieldPanel('enable_status_filter'),
        ], heading=_("Filter Options")),
        MultiFieldPanel([
            FieldPanel('default_hackathon'),
            FieldPanel('default_status'),
        ], heading=_("Default Filters")),
    ]

    search_fields = BasePage.search_fields + [
        index.SearchField('intro'),
    ]

    class Meta:
        verbose_name = _("Submission Index")
        verbose_name_plural = _("Submission Indexes")

    def get_context(self, request):
        context = super().get_context(request)

        # Start with all live, public submissions
        submissions = SubmissionPage.objects.live().public().order_by('-first_published_at')

        available_filters = {}
        applied_filters = {}

        # Hackathon filter
        if self.enable_hackathon_filter:
            from .hackathon import HackathonPage
            available_filters['hackathons'] = HackathonPage.objects.live()
            hackathon_id = request.GET.get('hackathon')
            # Only apply default if no explicit filter param in URL
            if 'hackathon' not in request.GET and self.default_hackathon:
                hackathon_id = str(self.default_hackathon.id)
            if hackathon_id:
                submissions = submissions.filter(hackathons__id=hackathon_id)
                applied_filters['hackathon'] = hackathon_id

        # Date range filter
        if self.enable_date_filter:
            available_filters['date_filter'] = True
            date_from = request.GET.get('from')
            date_to = request.GET.get('to')
            if date_from:
                submissions = submissions.filter(first_published_at__gte=date_from)
                applied_filters['from'] = date_from
            if date_to:
                submissions = submissions.filter(first_published_at__lte=date_to)
                applied_filters['to'] = date_to

        # Submitter filter
        if self.enable_submitter_filter:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            available_filters['submitters'] = User.objects.filter(
                submission_pages__isnull=False
            ).distinct()
            submitter_id = request.GET.get('submitter')
            if submitter_id:
                submissions = submissions.filter(submitter_id=submitter_id)
                applied_filters['submitter'] = submitter_id

        # Team filter
        if self.enable_team_filter:
            from synnovator.community.models import TeamProfilePage
            available_filters['teams'] = TeamProfilePage.objects.live().filter(
                submissions__isnull=False
            ).distinct()
            team_id = request.GET.get('team')
            if team_id:
                submissions = submissions.filter(team_profile_id=team_id)
                applied_filters['team'] = team_id

        # Status filter
        if self.enable_status_filter:
            available_filters['statuses'] = SUBMISSION_STATUS_CHOICES
            status = request.GET.get('status')
            # Only apply default if no explicit filter param in URL
            if 'status' not in request.GET and self.default_status:
                status = self.default_status
            if status:
                submissions = submissions.filter(verification_status=status)
                applied_filters['status'] = status

        # Pagination
        from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
        page_number = request.GET.get('page', 1)
        paginator = Paginator(submissions, settings.DEFAULT_PER_PAGE)
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        context['submissions'] = page.object_list
        context['paginator'] = paginator
        context['paginator_page'] = page
        context['is_paginated'] = page.has_other_pages()
        context['available_filters'] = available_filters
        context['applied_filters'] = applied_filters

        return context
