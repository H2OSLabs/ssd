## Section 5: Wagtail CMS Configuration

### 5.1 Philosophy

Store all hackathon configuration directly in Wagtail CMS using standard Django/Wagtail patterns. This provides:
- **Familiar admin interface** for COO - no Git knowledge required
- **No external dependencies** - all configuration in PostgreSQL
- **Reliable, transaction-safe** updates with Django ORM
- **Built-in versioning** via Wagtail page revisions
- **Fast iteration** - changes take effect immediately

Git integration will be added in Phase 3 for advanced use cases (see `spec/future/git-integrate.md`).

### 5.2 HackathonPage Configuration

HackathonPage uses Wagtail's `InlinePanel` to manage phases and prizes directly in the admin interface.

**File:** `synnovator/hackathons/models/hackathon.py`

```python
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

class HackathonPage(Page):
    """
    Wagtail page model for hackathon events.
    Uses InlinePanel for phases and prizes (standard Wagtail pattern).
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
        help_text="List of required roles (e.g., ['hacker', 'hustler'])"
    )

    # Scoring Configuration
    passing_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=80.0,
        help_text="Minimum score required for quest completion"
    )

    # Status
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

    # Panels for Wagtail Admin
    content_panels = Page.content_panels + [
        FieldPanel('description'),
        FieldPanel('cover_image'),
        InlinePanel('phases', label="Phases", help_text="Add timeline phases (registration, hacking, judging)"),
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
    Hackathon timeline phase (inline model).
    Examples: Registration, Team Formation, Hacking, Judging, Awards
    """

    hackathon = ParentalKey(
        HackathonPage,
        on_delete=models.CASCADE,
        related_name='phases'
    )

    title = models.CharField(
        max_length=200,
        help_text="Phase name (e.g., 'Team Formation', 'Hacking Period')"
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
    Hackathon prize (inline model).
    """

    hackathon = ParentalKey(
        HackathonPage,
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
        help_text="Ranking (1 = first place, 2 = second, etc.)"
    )

    monetary_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cash value in USD"
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

### 5.3 COO Workflow

**Step-by-step guide for creating a hackathon:**

1. **Navigate to Wagtail Admin**
   - Go to `/admin/`
   - Click "Pages" in sidebar
   - Navigate to desired parent page (e.g., `/hackathons/`)

2. **Create New HackathonPage**
   - Click "Add child page"
   - Select "Hackathon" page type
   - Fill in basic info:
     - Title: "GenAI Sprint 2026"
     - Description: Rich text summary
     - Cover image: Upload hero image

3. **Add Phases (using InlinePanel)**
   - Scroll to "Phases" section
   - Click "Add Phase" button
   - For each phase, enter:
     - Title: "Registration"
     - Description: "Sign up and complete profile"
     - Start date: 2026-02-01 00:00
     - End date: 2026-02-14 23:59
     - Order: 1
   - Repeat for:
     - Team Formation (order: 2)
     - Hacking (order: 3)
     - Judging (order: 4)
     - Awards (order: 5)

4. **Add Prizes (using InlinePanel)**
   - Scroll to "Prizes" section
   - Click "Add Prize" button
   - For each prize, enter:
     - Title: "Grand Prize"
     - Description: "Best overall solution"
     - Rank: 1
     - Monetary value: 10000.00
   - Repeat for Runner Up (rank: 2), Third Place (rank: 3), etc.

5. **Configure Team Settings**
   - Min team size: 2
   - Max team size: 5
   - Allow solo: No
   - Required roles: `["hacker", "hustler"]` (JSON format)

6. **Set Status**
   - Initially: "Draft"
   - When ready: "Upcoming" or "Registration Open"

7. **Publish**
   - Click "Publish" button
   - Page is now live at `/hackathons/genai-sprint-2026/`

**Total time:** < 10 minutes for experienced COO

### 5.4 Admin UI Enhancements

**File:** `synnovator/hackathons/wagtail_hooks.py`

```python
from wagtail import hooks
from django.templatetags.static import static
from django.utils.html import format_html


@hooks.register('insert_global_admin_css')
def global_admin_css():
    """Add custom CSS for hackathon admin"""
    return format_html(
        '<link rel="stylesheet" href="{}">',
        static('css/admin/hackathon.css')
    )


@hooks.register('construct_main_menu')
def hackathon_menu_item(request, menu_items):
    """Add Hackathon dashboard to admin menu"""
    from wagtail.admin.menu import MenuItem
    menu_items.append(
        MenuItem(
            'Hackathons',
            '/admin/hackathons/dashboard/',
            icon_name='calendar',
            order=200
        )
    )
```

### 5.5 Data Validation

**File:** `synnovator/hackathons/models/hackathon.py` (add to Phase model)

```python
def clean(self):
    """Validate phase dates"""
    from django.core.exceptions import ValidationError

    if self.end_date <= self.start_date:
        raise ValidationError({
            'end_date': 'End date must be after start date'
        })

    # Check for overlapping phases
    overlapping = self.hackathon.phases.exclude(pk=self.pk).filter(
        start_date__lt=self.end_date,
        end_date__gt=self.start_date
    )

    if overlapping.exists():
        raise ValidationError(
            f'Phase overlaps with: {overlapping.first().title}'
        )
```

### 5.6 Example Configuration

**GenAI Sprint 2026 Configuration:**

- **Hackathon Title:** GenAI Sprint 2026
- **Slug:** genai-sprint-2026
- **Status:** Registration Open

**Phases:**
1. Registration (Feb 1-14) - Sign up and complete profile
2. Team Formation (Feb 1-15) - Find co-founders
3. Hacking (Feb 15-17) - Build AI solution
4. Judging (Feb 17-19) - Present and get feedback
5. Awards (Feb 19) - Winners announced

**Prizes:**
1. Grand Prize ($10,000) - Best overall solution
2. Runner Up ($5,000) - Second place
3. Third Place ($2,500) - Third place
4. Best AI Innovation ($1,000) - Most creative use of AI

**Team Settings:**
- Min size: 2
- Max size: 5
- Required roles: Hacker, Hustler

All configured in < 10 minutes via Wagtail admin!

### 5.7 Benefits Over Git Integration (for MVP)

| Aspect | Wagtail CMS (MVP) | Git Integration (Phase 3) |
|--------|-------------------|---------------------------|
| COO Learning Curve | Familiar admin UI | Requires Git knowledge |
| Setup Time | < 10 minutes | ~30 minutes (repo setup) |
| External Dependencies | None | Git provider, webhooks |
| Failure Points | None | Network, Git API limits |
| Iteration Speed | Immediate | Commit → push → sync delay |
| Rollback | Wagtail revisions | Git revert + sync |
| Best For | MVP (< 100 participants) | Scale (1000+ participants) |

**When to add Git integration:** Phase 3, when platform reaches 100+ participants per hackathon and configuration versioning becomes critical. See `spec/future/git-integrate.md` for implementation guide.

---
