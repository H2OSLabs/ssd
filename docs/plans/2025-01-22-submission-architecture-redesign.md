# Submission Architecture Redesign

## Overview

Redesign the submission system to make `SubmissionPage` an independent, reusable page type that can be associated with multiple hackathons, with a dedicated `SubmissionIndexPage` for filtering and discovery.

## Current State

```
HomePage
├── HackathonIndexPage (/hackathons/)
│   └── HackathonPage
│       └── SubmissionPage (child of HackathonPage)
```

- `SubmissionPage` is a child page of `HackathonPage`
- One-to-one relationship via parent-child hierarchy
- No dedicated listing page for submissions

## Target State

```
HomePage
├── HackathonIndexPage (/hackathons/)
│   └── HackathonPage
│
└── SubmissionIndexPage (/submissions/)
    └── SubmissionPage
```

- `SubmissionPage` is independent under `SubmissionIndexPage`
- Many-to-many relationship with `HackathonPage`
- Dedicated listing page with configurable filters

---

## Data Model Changes

### SubmissionPage

**File:** `synnovator/hackathons/models/submission.py`

```python
class SubmissionPage(BasePage):
    # Many-to-many relationship with hackathons
    hackathons = models.ManyToManyField(
        'hackathons.HackathonPage',
        related_name='submissions',
        blank=True,
        verbose_name=_("Hackathons"),
        help_text=_("Hackathons this submission participates in")
    )

    # Submitter (one of these must be set)
    team_profile = models.ForeignKey(
        'community.TeamProfilePage',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='submissions',
        verbose_name=_("Team"),
        help_text=_("The team submitting this project")
    )

    submitter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='submissions',
        verbose_name=_("Submitter"),
        help_text=_("Individual user submitting this project")
    )

    # ... existing fields (tagline, content, verification_status, etc.) ...

    # Page configuration changes
    parent_page_types = ['hackathons.SubmissionIndexPage']  # Changed from HackathonPage
    subpage_types = []
```

### SubmissionIndexPage (New)

**File:** `synnovator/hackathons/models/submission.py`

```python
SUBMISSION_STATUS_CHOICES = [
    ('draft', _('Draft')),
    ('submitted', _('Submitted')),
    ('under_review', _('Under Review')),
    ('verified', _('Verified')),
    ('rejected', _('Rejected')),
    ('needs_revision', _('Needs Revision')),
]


class SubmissionIndexPage(BasePage):
    """Submission listing page with admin-configurable filters."""

    intro = RichTextField(blank=True, verbose_name=_("Introduction"))

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
        null=True, blank=True,
        on_delete=models.SET_NULL,
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

    class Meta:
        verbose_name = _("Submission Index")
        verbose_name_plural = _("Submission Indexes")

    def get_context(self, request):
        context = super().get_context(request)
        submissions = SubmissionPage.objects.live().public().order_by('-first_published_at')

        available_filters = {}

        # Hackathon filter
        if self.enable_hackathon_filter:
            from .hackathon import HackathonPage
            available_filters['hackathons'] = HackathonPage.objects.live()
            hackathon_id = request.GET.get('hackathon') or (
                self.default_hackathon.id if self.default_hackathon else None
            )
            if hackathon_id:
                submissions = submissions.filter(hackathons__id=hackathon_id)

        # Date range filter
        if self.enable_date_filter:
            available_filters['date_filter'] = True
            date_from = request.GET.get('from')
            date_to = request.GET.get('to')
            if date_from:
                submissions = submissions.filter(first_published_at__gte=date_from)
            if date_to:
                submissions = submissions.filter(first_published_at__lte=date_to)

        # Submitter filter
        if self.enable_submitter_filter:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            available_filters['submitters'] = User.objects.filter(
                submissions__isnull=False
            ).distinct()
            submitter_id = request.GET.get('submitter')
            if submitter_id:
                submissions = submissions.filter(submitter_id=submitter_id)

        # Team filter
        if self.enable_team_filter:
            from synnovator.community.models import TeamProfilePage
            available_filters['teams'] = TeamProfilePage.objects.live().filter(
                submissions__isnull=False
            ).distinct()
            team_id = request.GET.get('team')
            if team_id:
                submissions = submissions.filter(team_profile_id=team_id)

        # Status filter
        if self.enable_status_filter:
            available_filters['statuses'] = SUBMISSION_STATUS_CHOICES
            status = request.GET.get('status') or self.default_status
            if status:
                submissions = submissions.filter(verification_status=status)

        context['submissions'] = submissions
        context['available_filters'] = available_filters
        return context
```

### HackathonPage Changes

**File:** `synnovator/hackathons/models/hackathon.py`

```python
class HackathonPage(Page):
    # ... existing fields ...

    # === Submission Settings (New) ===
    submission_type = models.CharField(
        max_length=20,
        choices=[
            ('individual', _('Individual only')),
            ('team', _('Team only')),
            ('both', _('Both allowed')),
        ],
        default='both',
        verbose_name=_("Submission type")
    )

    max_submissions_per_participant = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Max submissions per participant"),
        help_text=_("0 = unlimited")
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

    # Page configuration changes
    parent_page_types = ['hackathons.HackathonIndexPage']
    subpage_types = []  # Remove SubmissionPage from here

    content_panels = Page.content_panels + [
        # ... existing panels ...
        MultiFieldPanel([
            FieldPanel('submission_type'),
            FieldPanel('max_submissions_per_participant'),
            FieldPanel('require_registration'),
            FieldPanel('restrict_to_submission_phase'),
            FieldPanel('allow_late_submission'),
            FieldPanel('allow_edit_after_submit'),
        ], heading=_("Submission Settings")),
    ]

    def can_submit(self, user=None, team_profile=None):
        """
        Check if user/team can submit based on admin configuration.
        Returns (bool, str) - (allowed, reason)
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
            return self.team_registrations.filter(team_profile=team_profile).exists()
        elif user:
            return self.registrations.filter(user=user).exists()
        return False

    def is_submission_open(self):
        """Check if currently in submission phase."""
        current_phase = self.get_current_phase()
        return current_phase and current_phase.phase_type == 'submission'
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `synnovator/hackathons/models/submission.py` | Modify `SubmissionPage`, add `SubmissionIndexPage` |
| `synnovator/hackathons/models/hackathon.py` | Add submission settings to `HackathonPage`, remove SubmissionPage from `subpage_types` |
| `synnovator/hackathons/models/__init__.py` | Export `SubmissionIndexPage` |
| `synnovator/hackathons/views.py` | Add submission creation view with validation |
| `synnovator/hackathons/urls.py` | Add submission creation route |

## Templates to Create

| Template | Purpose |
|----------|---------|
| `templates/hackathons/submission_index_page.html` | Submission listing with filters |
| `templates/hackathons/submission_create.html` | Submission creation form |

---

## Migration Plan

### Step 1: Add New Fields

```bash
uv run python manage.py makemigrations hackathons
```

### Step 2: Data Migration (if existing SubmissionPage data exists)

Create a data migration to:
1. Create SubmissionIndexPage under HomePage
2. Move existing SubmissionPage instances to new parent
3. Convert parent-child relationship to ManyToMany

```python
# Example data migration
from django.db import migrations

def migrate_submissions(apps, schema_editor):
    SubmissionPage = apps.get_model('hackathons', 'SubmissionPage')
    SubmissionIndexPage = apps.get_model('hackathons', 'SubmissionIndexPage')
    HomePage = apps.get_model('home', 'HomePage')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    # Get or create SubmissionIndexPage
    home = HomePage.objects.first()
    if not home:
        return

    content_type = ContentType.objects.get_for_model(SubmissionIndexPage)

    index_page, created = SubmissionIndexPage.objects.get_or_create(
        slug='submissions',
        defaults={
            'title': 'Submissions',
            'depth': home.depth + 1,
            'path': home.path + '0003',  # Adjust as needed
            'content_type': content_type,
        }
    )

    if created:
        home.add_child(instance=index_page)

    # Migrate existing submissions
    for submission in SubmissionPage.objects.all():
        old_parent = submission.get_parent()
        if old_parent and hasattr(old_parent.specific, 'hackathons'):
            # Add to many-to-many relationship
            submission.hackathons.add(old_parent.specific)
        # Move to new parent
        submission.move(index_page, pos='last-child')

class Migration(migrations.Migration):
    dependencies = [
        ('hackathons', 'XXXX_previous_migration'),
    ]

    operations = [
        migrations.RunPython(migrate_submissions, migrations.RunPython.noop),
    ]
```

### Step 3: Run Migrations

```bash
uv run python manage.py migrate
```

---

## URL Parameters for Filters

| Filter | Parameter | Example |
|--------|-----------|---------|
| Hackathon | `?hackathon=<id>` | `/submissions/?hackathon=5` |
| Date from | `?from=<date>` | `/submissions/?from=2024-01-01` |
| Date to | `?to=<date>` | `/submissions/?to=2024-12-31` |
| Submitter | `?submitter=<user_id>` | `/submissions/?submitter=10` |
| Team | `?team=<team_id>` | `/submissions/?team=3` |
| Status | `?status=<status>` | `/submissions/?status=verified` |

---

## Validation Flow

```
User clicks "Submit Project" on HackathonPage
    │
    ▼
HackathonPage.can_submit(user, team)
    │
    ├── Check submission_type config
    │   └── Reject if type mismatch
    │
    ├── Check require_registration config
    │   └── Reject if not registered
    │
    ├── Check max_submissions_per_participant config
    │   └── Reject if limit reached
    │
    ├── Check restrict_to_submission_phase config
    │   ├── If closed and allow_late_submission: Allow (marked late)
    │   └── If closed and not allow_late: Reject
    │
    └── Allow submission
            │
            ▼
        Create SubmissionPage under SubmissionIndexPage
        Add HackathonPage to hackathons ManyToMany field
```
