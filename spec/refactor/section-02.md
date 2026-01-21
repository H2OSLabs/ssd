## Section 2: Database Schema Design

### 2.1 HackathonPage Model

```python
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from django.db import models
from django.conf import settings
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
        'wagtailimages.Image',
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
        # Import from synnovator.utils.blocks
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
```

**Note:** Git integration removed for MVP. Phases and prizes managed via InlinePanel (standard Wagtail pattern). For Git sync in Phase 3, see `spec/future/git-integrate.md`.

### 2.2 Phase Model (Inline)

```python
from django.db import models
from modelcluster.models import ClusterableModel
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel

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
```

### 2.3 Prize Model (Inline)

```python
from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel

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
```

**Note:** `awarded_to` FK removed for MVP. Can be added later when needed for prize distribution.

### 2.4 Team Model

```python
from django.db import models
from django.conf import settings

class Team(models.Model):
    """
    Represents a team participating in a hackathon.
    """

    hackathon = models.ForeignKey(
        'HackathonPage',
        on_delete=models.CASCADE,
        related_name='teams'
    )

    name = models.CharField(
        max_length=200,
        help_text="Team name"
    )

    slug = models.SlugField(
        max_length=200,
        help_text="URL-friendly team identifier"
    )

    tagline = models.CharField(
        max_length=500,
        blank=True,
        help_text="Short team description"
    )

    # Team composition
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='TeamMember',
        related_name='hackathon_teams'
    )

    # Scoring
    final_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.0,
        help_text="Aggregated score from verification"
    )

    technical_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.0
    )

    commercial_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.0
    )

    operational_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.0
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('forming', 'Forming'),
            ('ready', 'Ready'),
            ('submitted', 'Submitted'),
            ('verified', 'Verified'),
            ('disqualified', 'Disqualified'),
        ],
        default='forming'
    )

    is_seeking_members = models.BooleanField(
        default=True,
        help_text="Show in team formation page"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['hackathon', 'slug']]
        ordering = ['-final_score', 'name']

    def __str__(self):
        return f"{self.name} ({self.hackathon.title})"

    def get_leader(self):
        """Get team leader (first member with is_leader=True)"""
        return self.membership.filter(is_leader=True).first()

    def has_required_roles(self):
        """Check if team meets hackathon's required role composition"""
        required = set(self.hackathon.required_roles)
        current = set(self.membership.values_list('role', flat=True))
        return required.issubset(current)

    def can_add_member(self):
        """Check if team can accept new members"""
        return (
            self.members.count() < self.hackathon.max_team_size and
            self.status == 'forming'
        )
```

### 2.5 TeamMember Model (Through Model)

```python
from django.db import models
from django.conf import settings

class TeamMember(models.Model):
    """
    Through model for Team-User M2M relationship.
    Tracks role, contribution, and leadership.
    """

    team = models.ForeignKey(
        'Team',
        on_delete=models.CASCADE,
        related_name='membership'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='team_memberships'
    )

    role = models.CharField(
        max_length=50,
        choices=[
            ('hacker', 'Hacker (Engineer)'),
            ('hipster', 'Hipster (Designer/UX)'),
            ('hustler', 'Hustler (Business/Marketing)'),
            ('mentor', 'Mentor'),
        ],
        help_text="Team role"
    )

    is_leader = models.BooleanField(
        default=False,
        help_text="Team captain/leader"
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['team', 'user']]
        ordering = ['-is_leader', 'joined_at']

    def __str__(self):
        leader = " (Leader)" if self.is_leader else ""
        return f"{self.user.get_full_name()} - {self.get_role_display()}{leader}"
```

###  2.6 Quest Model

```python
from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField

class Quest(models.Model):
    """
    Represents a Dojo challenge that can be standalone or hackathon-specific.
    Quests award XP and serve as skill verification.
    """

    title = models.CharField(
        max_length=200,
        help_text="Quest name"
    )

    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text="URL-friendly identifier"
    )

    description = RichTextField(
        help_text="Challenge description and objectives"
    )

    # Quest type and difficulty
    quest_type = models.CharField(
        max_length=20,
        choices=[
            ('technical', 'Technical (Hacker)'),
            ('commercial', 'Commercial (Hustler)'),
            ('operational', 'Operational (Hipster)'),
            ('mixed', 'Mixed'),
        ],
        default='technical'
    )

    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert'),
        ],
        default='intermediate'
    )

    # Gamification
    xp_reward = models.PositiveIntegerField(
        default=100,
        help_text="XP awarded upon completion"
    )

    estimated_time_minutes = models.PositiveIntegerField(
        default=60,
        help_text="Estimated completion time"
    )

    # Association
    hackathon = models.ForeignKey(
        'HackathonPage',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='quests',
        help_text="If set, quest is specific to this hackathon"
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Quest is available for attempts"
    )

    # Metadata
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Skill tags (e.g., ['python', 'machine-learning', 'api'])"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Quest"
        verbose_name_plural = "Quests"

    def __str__(self):
        return f"{self.title} ({self.get_difficulty_display()})"

    def get_completion_rate(self):
        """Calculate percentage of users who completed this quest"""
        total_attempts = self.submissions.count()
        if total_attempts == 0:
            return 0
        completed = self.submissions.filter(verification_status='passed').count()
        return (completed / total_attempts) * 100
```

### 2.7 Submission Model

```python
from django.db import models
from django.conf import settings
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

    panels = [
        FieldPanel('verification_status'),
        FieldPanel('score'),
        FieldPanel('feedback'),
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
        from django.core.exceptions import ValidationError
        # Ensure exactly one submitter
        if not ((self.user and not self.team) or (self.team and not self.user)):
            raise ValidationError("Submission must have either a user OR a team, not both.")
        # Ensure exactly one target
        if not ((self.quest and not self.hackathon) or (self.hackathon and not self.quest)):
            raise ValidationError("Submission must be for either a quest OR a hackathon, not both.")
        # Ensure at least one submission method
        if not self.submission_file and not self.submission_url:
            raise ValidationError("Submission must include a file OR a URL.")
```

**Note:** Simplified for manual verification workflow. Automated webhook verification can be added in Phase 3 (see `spec/future/git-integrate.md`).

### 2.8 VerificationLog Model (Optional - Phase 3)

**Note:** VerificationLog is not needed for MVP manual verification workflow. This model will be implemented in Phase 3 when automated webhook verification is added.

For Phase 3 webhook verification, this model will store:
- Webhook audit trail from CI/CD providers (GitHub Actions, GitLab CI)
- HMAC signature verification results
- Complete webhook payloads for compliance and debugging
- Processing status and errors

See `spec/future/git-integrate.md` for complete VerificationLog implementation.

### 2.9 User Model Extensions

```python
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Extended user model with hackathon-specific fields.
    This extends the existing synnovator.users.User model.
    """

    # Profile
    preferred_role = models.CharField(
        max_length=50,
        choices=[
            ('hacker', 'Hacker (Engineer)'),
            ('hipster', 'Hipster (Designer/UX)'),
            ('hustler', 'Hustler (Business/Marketing)'),
            ('mentor', 'Mentor'),
            ('any', 'Flexible'),
        ],
        blank=True,
        help_text="Preferred team role"
    )

    bio = models.TextField(
        max_length=500,
        blank=True,
        help_text="Short bio for team matching"
    )

    skills = models.JSONField(
        default=list,
        blank=True,
        help_text="List of skills (e.g., ['Python', 'React', 'ML'])"
    )

    # Gamification
    xp_points = models.PositiveIntegerField(
        default=0,
        help_text="Total experience points earned"
    )

    reputation_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.0,
        help_text="Quality metric based on submissions and peer ratings"
    )

    level = models.PositiveIntegerField(
        default=1,
        help_text="User level (derived from XP)"
    )

    # Onboarding
    profile_completed = models.BooleanField(
        default=False,
        help_text="User has completed profile setup"
    )

    onboarding_completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # Preferences
    is_seeking_team = models.BooleanField(
        default=False,
        help_text="Show in team formation matching"
    )

    notification_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="Email/push notification settings"
    )

    class Meta(AbstractUser.Meta):
        swappable = 'AUTH_USER_MODEL'

    def calculate_level(self):
        """Calculate level from XP (100 XP per level)"""
        return (self.xp_points // 100) + 1

    def award_xp(self, points, reason=""):
        """Add XP and recalculate level"""
        self.xp_points += points
        self.level = self.calculate_level()
        self.save()
        # TODO: Create XPTransaction record for audit trail

    def get_verified_skills(self):
        """Return skills verified through quest completions"""
        completed_quests = Submission.objects.filter(
            user=self,
            quest__isnull=False,
            verification_status='verified'
        ).select_related('quest')

        skills = set()
        for submission in completed_quests:
            if submission.quest and submission.quest.tags:
                skills.update(submission.quest.tags)
        return list(skills)
```

**Note:** OAuth fields (github_username, gitlab_username, oauth tokens) removed for MVP. Git integration will be added in Phase 3 (see `spec/future/git-integrate.md`).

---

