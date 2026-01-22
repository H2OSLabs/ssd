from django.db import models
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import gettext_lazy as _
from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.search import index
from wagtail import blocks
from modelcluster.fields import ParentalKey

from synnovator.utils.models import BasePage


class HackathonIndexPage(BasePage):
    """
    Index page for listing hackathons with configurable filtering.
    Follows Wagtail Index Page pattern - managed in admin, part of page tree.

    Filter modes:
    - all: Show all hackathons
    - in_progress: Show only hackathons with status='in_progress'
    - by_tag: Show hackathons matching the specified filter_tag

    Usage:
    - /hackathons/ → all hackathons (filter_mode='all')
    - /hackathons/ongoing/ → in-progress hackathons (filter_mode='in_progress')
    - /hackathons/enterprise/ → enterprise hackathons (filter_mode='by_tag', filter_tag='from_enterprise')
    """

    FILTER_MODE_CHOICES = [
        ('all', 'All Hackathons'),
        ('in_progress', 'In Progress Only'),
        ('by_tag', 'By Tag'),
    ]

    # Editable intro content
    introduction = RichTextField(
        blank=True,
        features=["bold", "italic", "link"],
        help_text="Introduction text displayed at the top of the hackathons listing page"
    )

    # Featured hackathon (optional)
    featured_hackathon = models.ForeignKey(
        'HackathonPage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Select a hackathon to feature at the top of the page"
    )

    # Filter configuration
    filter_mode = models.CharField(
        max_length=20,
        choices=FILTER_MODE_CHOICES,
        default='all',
        help_text="How to filter hackathons on this index page"
    )

    filter_tag = models.CharField(
        max_length=100,
        blank=True,
        help_text="Tag to filter by (only used when filter_mode is 'by_tag'). E.g., 'from_enterprise'"
    )

    # Page type constraints
    subpage_types = ['hackathons.HackathonPage']
    # Removed max_count = 1 to allow multiple index pages with different filters

    search_fields = BasePage.search_fields + [
        index.SearchField("introduction")
    ]

    content_panels = BasePage.content_panels + [
        FieldPanel('introduction'),
        FieldPanel('featured_hackathon'),
        MultiFieldPanel([
            FieldPanel('filter_mode'),
            FieldPanel('filter_tag'),
        ], heading="Filter Settings"),
    ]

    class Meta:
        verbose_name = "Hackathon Index Page"
        verbose_name_plural = "Hackathon Index Pages"

    def paginate_queryset(self, queryset, request):
        """Paginate the queryset."""
        page_number = request.GET.get("page", 1)
        paginator = Paginator(queryset, settings.DEFAULT_PER_PAGE)
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        return (paginator, page, page.object_list, page.has_other_pages())

    def get_filtered_hackathons(self):
        """
        Get hackathons queryset based on filter_mode configuration.

        Returns:
            QuerySet: Filtered HackathonPage queryset
        """
        hackathons = HackathonPage.objects.live().public().select_related(
            'cover_image'
        ).order_by('-first_published_at')

        if self.filter_mode == 'in_progress':
            hackathons = hackathons.filter(status='in_progress')
        elif self.filter_mode == 'by_tag' and self.filter_tag:
            # Filter by tag - use icontains for SQLite compatibility
            # For PostgreSQL in production, consider using tags__contains=[self.filter_tag]
            hackathons = hackathons.filter(tags__icontains=self.filter_tag)

        return hackathons

    def get_context(self, request, *args, **kwargs):
        """Add hackathons queryset to template context with pagination"""
        context = super().get_context(request, *args, **kwargs)

        # Get filtered hackathons based on index page configuration
        hackathons = self.get_filtered_hackathons()

        # Separate featured hackathon from regular list
        if self.featured_hackathon and self.featured_hackathon.live:
            context['featured'] = self.featured_hackathon
            # Exclude featured from regular list
            hackathons = hackathons.exclude(id=self.featured_hackathon.id)

        # Paginate hackathons
        paginator, page, _object_list, is_paginated = self.paginate_queryset(
            hackathons, request
        )
        context['paginator'] = paginator
        context['paginator_page'] = page
        context['is_paginated'] = is_paginated
        context['hackathons'] = page.object_list

        # Add filter context for template
        context['filter_mode'] = self.filter_mode
        context['filter_tag'] = self.filter_tag

        return context


class QuestIndexPage(BasePage):
    """
    Index page for listing all Quest snippets.
    Follows Wagtail Index Page pattern - managed in admin, part of page tree.
    
    Note: Quest remains a Snippet, not a Page. This IndexPage queries Snippets.
    """
    
    # Editable intro content
    introduction = RichTextField(
        blank=True,
        features=["bold", "italic", "link"],
        help_text="Introduction text displayed at the top of the quests listing page"
    )
    
    # Featured quest (optional)
    featured_quest = models.ForeignKey(
        'Quest',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Select a quest to feature at the top of the page"
    )
    
    # Page type constraints - no subpages since Quest is a Snippet
    subpage_types = []
    max_count = 1  # Only allow one index page
    
    search_fields = BasePage.search_fields + [
        index.SearchField("introduction")
    ]
    
    content_panels = BasePage.content_panels + [
        FieldPanel('introduction'),
        FieldPanel('featured_quest'),
    ]
    
    class Meta:
        verbose_name = "Quest Index Page"
        verbose_name_plural = "Quest Index Pages"
    
    def paginate_queryset(self, queryset, request):
        """Paginate the queryset."""
        page_number = request.GET.get("page", 1)
        paginator = Paginator(queryset, settings.DEFAULT_PER_PAGE)
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        return (paginator, page, page.object_list, page.has_other_pages())
    
    def get_context(self, request, *args, **kwargs):
        """Add quests queryset to template context with filtering, pagination, and recommendations"""
        context = super().get_context(request, *args, **kwargs)
        
        # Import here to avoid circular imports
        from .quest import Quest
        from .submission import Submission
        
        # Get all active quests
        quests = Quest.objects.filter(is_active=True)
        
        # Parse and apply filters (same logic as quest_list view)
        difficulty_filters = request.GET.getlist('difficulty')
        type_filters = request.GET.getlist('type')
        tag_filters = request.GET.getlist('tags')
        xp_min = request.GET.get('xp_min')
        xp_max = request.GET.get('xp_max')
        
        # Apply filters
        if difficulty_filters:
            difficulty_map = {
                'easy': 'beginner',
                'medium': 'intermediate',
                'hard': 'advanced',
            }
            model_difficulties = [difficulty_map.get(d, d) for d in difficulty_filters]
            quests = quests.filter(difficulty__in=model_difficulties)
        
        if type_filters:
            type_map = {
                'coding': 'technical',
                'design': 'operational',
                'research': 'commercial',
                'testing': 'technical',
                'documentation': 'operational',
            }
            model_types = [type_map.get(t, t) for t in type_filters]
            quests = quests.filter(quest_type__in=model_types)
        
        if tag_filters:
            for tag in tag_filters:
                quests = quests.filter(tags__icontains=tag)
        
        if xp_min:
            quests = quests.filter(xp_reward__gte=int(xp_min))
        
        if xp_max:
            quests = quests.filter(xp_reward__lte=int(xp_max))
        
        # Separate featured quest from regular list
        if self.featured_quest and self.featured_quest.is_active:
            context['featured'] = self.featured_quest
            quests = quests.exclude(id=self.featured_quest.id)
        
        # Paginate quests
        paginator, page, _object_list, is_paginated = self.paginate_queryset(quests, request)
        context['paginator'] = paginator
        context['paginator_page'] = page
        context['is_paginated'] = is_paginated
        
        # Add computed fields to quests for template
        quests_with_data = []
        for quest in page.object_list:
            quest.url = f'/hackathons/quests/{quest.slug}/'
            quest.estimated_hours = quest.estimated_time_minutes / 60 if quest.estimated_time_minutes else None
            quest.skills = quest.tags or []
            quests_with_data.append(quest)
        context['quests'] = quests_with_data
        
        # Build filters context
        filters = {
            'difficulty': difficulty_filters,
            'type': type_filters,
            'tags': tag_filters,
            'xp_min': xp_min,
            'xp_max': xp_max,
        }
        has_filters = any([difficulty_filters, type_filters, tag_filters, xp_min, xp_max])
        context['filters'] = filters if has_filters else None
        
        # Build user stats if authenticated
        user_stats = {
            'completed_count': 0,
            'total_xp': 0,
            'current_streak': 0,
        }
        if request.user.is_authenticated:
            completed = Submission.objects.filter(
                user=request.user,
                quest__isnull=False,
                verification_status='verified'
            )
            user_stats['completed_count'] = completed.count()
            from django.db.models import Sum
            total_xp = completed.select_related('quest').aggregate(
                total=Sum('quest__xp_reward')
            )['total']
            user_stats['total_xp'] = total_xp or 0
        context['user_stats'] = user_stats
        
        # Get recommended quests
        recommended_quests = []
        if request.user.is_authenticated:
            user_skills = request.user.skills or []
            if user_skills:
                for skill in user_skills[:3]:
                    matching = Quest.objects.filter(
                        is_active=True,
                        tags__icontains=skill
                    ).exclude(
                        submissions__user=request.user,
                        submissions__verification_status='verified'
                    )[:2]
                    recommended_quests.extend(matching)
            if not recommended_quests:
                recommended_quests = list(Quest.objects.filter(
                    is_active=True,
                    difficulty='beginner'
                ).exclude(
                    submissions__user=request.user,
                    submissions__verification_status='verified'
                )[:5])
        else:
            recommended_quests = list(Quest.objects.filter(
                is_active=True,
                difficulty='beginner'
            )[:5])
        context['recommended_quests'] = recommended_quests[:5]
        
        return context


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

    # Tags for categorization and filtering
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags for categorization (e.g., ['from_enterprise', 'ai', 'blockchain'])"
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

    # === Submission Settings ===
    submission_type = models.CharField(
        max_length=20,
        choices=[
            ('individual', _('Individual only')),
            ('team', _('Team only')),
            ('both', _('Both allowed')),
        ],
        default='both',
        verbose_name=_("Submission type"),
        help_text=_("Who can submit to this hackathon")
    )

    max_submissions_per_participant = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Max submissions per participant"),
        help_text=_("Maximum submissions allowed per user/team. 0 = unlimited")
    )

    require_registration = models.BooleanField(
        default=True,
        verbose_name=_("Require registration"),
        help_text=_("Participant must register before submitting")
    )

    restrict_to_submission_phase = models.BooleanField(
        default=True,
        verbose_name=_("Restrict to submission phase"),
        help_text=_("Only allow submissions during submission phase")
    )

    allow_late_submission = models.BooleanField(
        default=False,
        verbose_name=_("Allow late submissions"),
        help_text=_("Accept submissions after deadline (may be marked as late)")
    )

    allow_edit_after_submit = models.BooleanField(
        default=True,
        verbose_name=_("Allow editing after submission"),
        help_text=_("Participants can edit their submission after submitting")
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
        FieldPanel('tags'),
        FieldPanel('body'),
        InlinePanel('phases', label="Hackathon Phases", help_text="Add timeline phases (registration, hacking, judging, etc.)"),
        InlinePanel('prizes', label="Prizes", help_text="Add prizes and awards"),
        InlinePanel('rules', label="Competition Rules", help_text="Define competition rules and constraints"),
        MultiFieldPanel([
            FieldPanel('min_team_size'),
            FieldPanel('max_team_size'),
            FieldPanel('allow_solo'),
            FieldPanel('required_roles'),
        ], heading="Team Settings"),
        MultiFieldPanel([
            FieldPanel('passing_score'),
        ], heading="Scoring Settings"),
        MultiFieldPanel([
            FieldPanel('submission_type'),
            FieldPanel('max_submissions_per_participant'),
            FieldPanel('require_registration'),
            FieldPanel('restrict_to_submission_phase'),
            FieldPanel('allow_late_submission'),
            FieldPanel('allow_edit_after_submit'),
        ], heading=_("Submission Settings")),
        FieldPanel('status'),
        InlinePanel('team_registrations', label=_("Registered Teams")),
    ]

    # Page type constraints - only allow as child of HackathonIndexPage
    parent_page_types = ['hackathons.HackathonIndexPage']
    # SubmissionPage is now under SubmissionIndexPage, not HackathonPage
    subpage_types = []

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

    def is_registration_open(self):
        """Check if hackathon is accepting registrations"""
        return self.status in ['upcoming', 'registration_open']

    def is_team_registered(self, team_profile):
        """Check if a team is registered for this hackathon"""
        return self.team_registrations.filter(team_profile=team_profile).exists()

    def register_team(self, team_profile):
        """
        Register a team for this hackathon.
        Creates a TeamRegistration linking the team to this hackathon.
        """
        if not self.is_registration_open():
            raise ValueError(_("Hackathon is not accepting registrations"))

        if self.is_team_registered(team_profile):
            raise ValueError(_("Team is already registered"))

        return TeamRegistration.objects.create(
            hackathon=self,
            team_profile=team_profile
        )

    def get_registered_teams(self):
        """Get all registered teams"""
        return self.team_registrations.filter(
            status='approved'
        ).select_related('team_profile')

    def get_submissions(self):
        """Get all project submissions for this hackathon"""
        from .submission import SubmissionPage
        return SubmissionPage.objects.live().filter(hackathons=self)

    def can_submit(self, user=None, team_profile=None):
        """
        Check if user/team can submit based on admin configuration.

        Args:
            user: User instance for individual submission
            team_profile: TeamProfilePage instance for team submission

        Returns:
            tuple: (allowed: bool, reason: str)
        """
        # 1. Submission type check
        if self.submission_type == 'individual' and team_profile:
            return False, _("This hackathon only accepts individual submissions")
        if self.submission_type == 'team' and not team_profile:
            return False, _("This hackathon only accepts team submissions")

        # 2. Registration check (if enabled)
        if self.require_registration:
            if not self.is_participant_registered(user, team_profile):
                return False, _("You must register before submitting")

        # 3. Submission count check (if configured > 0)
        if self.max_submissions_per_participant > 0:
            count = self.get_submission_count(user, team_profile)
            if count >= self.max_submissions_per_participant:
                return False, _("Maximum submissions reached")

        # 4. Phase check (if enabled)
        if self.restrict_to_submission_phase:
            if not self.is_submission_open():
                if self.allow_late_submission:
                    return True, _("Late submission")
                return False, _("Submissions are closed")

        return True, ""

    def get_submission_count(self, user=None, team_profile=None):
        """Get submission count for user/team in this hackathon."""
        from .submission import SubmissionPage
        qs = SubmissionPage.objects.live().filter(hackathons=self)
        if team_profile:
            return qs.filter(team_profile=team_profile).count()
        elif user:
            return qs.filter(submitter=user).count()
        return 0

    def is_participant_registered(self, user=None, team_profile=None):
        """Check if user/team is registered for this hackathon."""
        if team_profile:
            return self.team_registrations.filter(
                team_profile=team_profile,
                status='approved'
            ).exists()
        elif user:
            # Check if user is a member of any registered team
            from synnovator.community.models import TeamProfilePage
            user_teams = TeamProfilePage.objects.filter(memberships__user=user)
            return self.team_registrations.filter(
                team_profile__in=user_teams,
                status='approved'
            ).exists()
        return False

    def is_submission_open(self):
        """Check if currently in submission phase."""
        current_phase = self.get_current_phase()
        if not current_phase:
            # If no phases defined, check status
            return self.status == 'in_progress'
        # Check if phase type indicates submission is allowed
        # Common phase types that allow submission
        submission_phase_keywords = ['submission', 'hacking', 'development', 'building']
        phase_title_lower = current_phase.title.lower()
        return any(keyword in phase_title_lower for keyword in submission_phase_keywords)


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

    # Required quests for phase completion
    required_quests = models.ManyToManyField(
        'Quest',
        blank=True,
        related_name='phases',
        help_text="Quests that must be completed to advance from this phase"
    )

    panels = [
        FieldPanel('title'),
        FieldPanel('description'),
        FieldPanel('start_date'),
        FieldPanel('end_date'),
        FieldPanel('order'),
        FieldPanel('required_quests'),
    ]

    class Meta:
        ordering = ['order', 'start_date']

    def __str__(self):
        return f"{self.title} ({self.start_date.strftime('%Y-%m-%d')})"

    def is_active(self):
        from django.utils import timezone
        now = timezone.now()
        return self.start_date <= now <= self.end_date

    def check_quest_completion(self, user_or_team):
        """
        Check if user or team has completed all required quests for this phase.
        
        Args:
            user_or_team: User instance or Team instance
            
        Returns:
            tuple: (is_complete: bool, message: str)
        """
        required_quests = self.required_quests.filter(is_active=True)
        if not required_quests.exists():
            return True, "No quests required for this phase"
        
        # Determine if we're checking for a user or team
        from synnovator.hackathons.models import Submission
        
        if hasattr(user_or_team, 'username'):  # User instance
            completed_quests = Submission.objects.filter(
                quest__in=required_quests,
                verification_status='verified',
                user=user_or_team
            ).values_list('quest_id', flat=True).distinct()
        elif hasattr(user_or_team, 'name'):  # Team instance
            completed_quests = Submission.objects.filter(
                quest__in=required_quests,
                verification_status='verified',
                team=user_or_team
            ).values_list('quest_id', flat=True).distinct()
        else:
            return False, "Invalid user_or_team parameter"
        
        missing = required_quests.exclude(id__in=completed_quests)
        if missing.exists():
            missing_titles = ', '.join(missing.values_list('title', flat=True))
            return False, f"Missing quests: {missing_titles}"
        return True, "All required quests completed"


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


class TeamRegistration(Orderable):
    """
    Represents a team's registration for a hackathon.

    This is the simplified design where:
    - Registering for a hackathon = Adding a TeamRegistration linking TeamProfilePage to HackathonPage
    - Team members can then submit projects (SubmissionPage) under the hackathon

    Uses Orderable to maintain order and ParentalKey for InlinePanel integration.
    """

    hackathon = ParentalKey(
        'HackathonPage',
        on_delete=models.CASCADE,
        related_name='team_registrations'
    )

    team_profile = models.ForeignKey(
        'community.TeamProfilePage',
        on_delete=models.CASCADE,
        related_name='hackathon_registrations',
        verbose_name=_("Team")
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

    # Optional notes
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Team's notes or motivation for joining")
    )

    # Timestamps
    registered_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Registered At")
    )

    panels = [
        FieldPanel('team_profile'),
        FieldPanel('status'),
        FieldPanel('notes'),
    ]

    class Meta:
        unique_together = [['hackathon', 'team_profile']]
        ordering = ['-registered_at']
        verbose_name = _("Team Registration")
        verbose_name_plural = _("Team Registrations")

    def __str__(self):
        return f"{self.team_profile.title} - {self.hackathon.title} ({self.get_status_display()})"

    def approve(self):
        """Approve the registration"""
        self.status = 'approved'
        self.save()

    def reject(self):
        """Reject the registration"""
        self.status = 'rejected'
        self.save()

    def withdraw(self):
        """Withdraw the registration"""
        self.status = 'withdrawn'
        self.save()
