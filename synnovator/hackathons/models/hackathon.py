from django.db import models
from django.conf import settings
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail import blocks
from modelcluster.fields import ParentalKey


class HackathonPage(Page):
    """
    Wagtail page model for hackathon events.
    Uses standard Wagtail patterns with InlinePanel for phases and prizes.
    """

    # Basic Information
    description = RichTextField(
        blank=True,
        help_text="Brief description of the hackathon"
    )

    cover_image = models.ForeignKey(
        'images.CustomImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    # Team Configuration
    min_team_size = models.PositiveIntegerField(
        default=2,
        help_text="Minimum number of team members"
    )

    max_team_size = models.PositiveIntegerField(
        default=5,
        help_text="Maximum number of team members"
    )

    allow_solo = models.BooleanField(
        default=False,
        help_text="Allow individual participants without teams"
    )

    required_roles = models.JSONField(
        default=list,
        blank=True,
        help_text="List of required roles for team composition (e.g., ['hacker', 'hustler'])"
    )

    # Scoring Configuration
    passing_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=80.0,
        help_text="Minimum score required for quest completion"
    )

    # Status and Visibility
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('upcoming', 'Upcoming'),
            ('registration_open', 'Registration Open'),
            ('in_progress', 'In Progress'),
            ('judging', 'Judging'),
            ('completed', 'Completed'),
            ('archived', 'Archived'),
        ],
        default='draft'
    )

    # StreamField for flexible content
    body = StreamField([
        ('heading', blocks.CharBlock(form_classname="title")),
        ('paragraph', blocks.RichTextBlock()),
    ], blank=True, use_json_field=True)

    # Panels for Wagtail Admin
    content_panels = Page.content_panels + [
        FieldPanel('description'),
        FieldPanel('cover_image'),
        FieldPanel('body'),
        InlinePanel('phases', label="Hackathon Phases", help_text="Add timeline phases (registration, hacking, judging, etc.)"),
        InlinePanel('prizes', label="Prizes", help_text="Add prizes and awards"),
        MultiFieldPanel([
            FieldPanel('min_team_size'),
            FieldPanel('max_team_size'),
            FieldPanel('allow_solo'),
            FieldPanel('required_roles'),
        ], heading="Team Settings"),
        MultiFieldPanel([
            FieldPanel('passing_score'),
        ], heading="Scoring Settings"),
        FieldPanel('status'),
    ]

    class Meta:
        verbose_name = "Hackathon"
        verbose_name_plural = "Hackathons"

    def get_current_phase(self):
        """Get current active phase based on datetime"""
        from django.utils import timezone
        now = timezone.now()
        return self.phases.filter(
            start_date__lte=now,
            end_date__gte=now
        ).first()

    def get_leaderboard(self, limit=10):
        """Get top teams ordered by score"""
        return self.teams.filter(
            status__in=['submitted', 'verified']
        ).order_by('-final_score')[:limit]


class Phase(models.Model):
    """
    Represents a timeline phase within a hackathon.
    Inline model managed via InlinePanel in HackathonPage.
    Examples: Registration, Team Formation, Hacking, Judging, Awards
    """

    hackathon = ParentalKey(
        'HackathonPage',
        on_delete=models.CASCADE,
        related_name='phases'
    )

    title = models.CharField(
        max_length=200,
        help_text="Display name for phase (e.g., 'Team Formation', 'Hacking Period')"
    )

    description = models.TextField(
        blank=True,
        help_text="Phase description and objectives"
    )

    start_date = models.DateTimeField(
        help_text="Phase start datetime (UTC)"
    )

    end_date = models.DateTimeField(
        help_text="Phase end datetime (UTC)"
    )

    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers first)"
    )

    requirements = models.JSONField(
        default=dict,
        blank=True,
        help_text="Optional phase-specific requirements as JSON"
    )

    panels = [
        FieldPanel('title'),
        FieldPanel('description'),
        FieldPanel('start_date'),
        FieldPanel('end_date'),
        FieldPanel('order'),
    ]

    class Meta:
        ordering = ['order', 'start_date']

    def __str__(self):
        return f"{self.title} ({self.start_date.strftime('%Y-%m-%d')})"

    def is_active(self):
        from django.utils import timezone
        now = timezone.now()
        return self.start_date <= now <= self.end_date


class Prize(models.Model):
    """
    Represents awards and prizes for hackathon winners.
    Inline model managed via InlinePanel in HackathonPage.
    """

    hackathon = ParentalKey(
        'HackathonPage',
        on_delete=models.CASCADE,
        related_name='prizes'
    )

    title = models.CharField(
        max_length=200,
        help_text="Prize name (e.g., 'First Place', 'Best AI Solution')"
    )

    description = models.TextField(
        blank=True,
        help_text="Prize details and benefits"
    )

    rank = models.PositiveIntegerField(
        default=1,
        help_text="Ranking (1 = first place, 2 = second place, etc.)"
    )

    monetary_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cash value in USD"
    )

    benefits = models.JSONField(
        default=list,
        blank=True,
        help_text="Non-monetary benefits as JSON array (e.g., ['Incubation access', 'Mentorship'])"
    )

    panels = [
        FieldPanel('title'),
        FieldPanel('description'),
        FieldPanel('rank'),
        FieldPanel('monetary_value'),
    ]

    class Meta:
        ordering = ['rank']

    def __str__(self):
        return f"{self.title} - {self.hackathon.title}"
