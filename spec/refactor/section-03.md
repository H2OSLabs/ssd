## Section 3: App Structure & Organization

### 3.1 Recommended App Structure

**Consolidated `synnovator.hackathons` app** containing all hackathon-related functionality:

```
synnovator/hackathons/
├── __init__.py
├── apps.py
├── admin.py                    # Wagtail ModelAdmin for submissions
├── models/
│   ├── __init__.py
│   ├── hackathon.py            # HackathonPage, Phase, Prize (inline models)
│   ├── team.py                 # Team, TeamMember
│   ├── quest.py                # Quest
│   └── submission.py           # Submission (file upload + URL support)
├── views.py                    # Team formation, submission views
├── forms.py                    # Submission forms, team creation forms
├── matching.py                 # Team matching algorithms (Phase 2)
├── scoring.py                  # Score calculation and XP awarding
├── templates/
│   └── hackathons/
│       ├── hackathon_page.html
│       ├── hackathon_listing_page.html
│       ├── team_profile.html
│       ├── team_formation.html
│       └── quest_listing.html
├── tests/
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_scoring.py
│   └── test_matching.py
└── wagtail_hooks.py            # Wagtail admin hooks (custom dashboard widgets)
```

**Removed from MVP:**
- `config_sync.py` - Git YAML parsing (Phase 3)
- `webhooks.py` - CI/CD webhook handlers (Phase 3)
- `verification.py` - Automated verification engine (Phase 3)
- `api/` directory - REST API (Phase 3)
- `management/commands/` - Git sync commands (Phase 3)

**See `spec/future/git-integrate.md` for Phase 3 additions.**

### 3.2 Existing Apps to Keep

| App | Purpose | Changes Needed |
|-----|---------|----------------|
| `synnovator.news` | Platform announcements | Rename to `announcements` or keep as-is |
| `synnovator.events` | Legacy/non-hackathon events | Keep for workshops, meetups |
| `synnovator.users` | User authentication | Extend User model with profile fields |
| `synnovator.home` | Homepage | Update to feature hackathons, not blog |
| `synnovator.utils` | Shared components | Keep blocks, models unchanged |
| `synnovator.images` | Image handling | Keep unchanged |
| `synnovator.search` | Search functionality | Update to index hackathons, teams, quests |
| `synnovator.navigation` | Menus | Update links to hackathon sections |

### 3.3 Settings Configuration

**Add to `synnovator/settings/base.py`:**

```python
INSTALLED_APPS = [
    # ... existing apps ...
    'synnovator.hackathons',  # Add this
]

# Hackathon-specific settings
HACKATHON_MAX_TEAM_SIZE = 10
HACKATHON_DEFAULT_MIN_TEAM_SIZE = 2
HACKATHON_DEFAULT_MAX_TEAM_SIZE = 5
HACKATHON_XP_PER_QUEST = 100
HACKATHON_PASSING_SCORE = 80.0  # Default passing score

# File upload settings
HACKATHON_MAX_SUBMISSION_SIZE = 50 * 1024 * 1024  # 50 MB
HACKATHON_ALLOWED_FILE_TYPES = [
    '.zip', '.tar.gz', '.pdf', '.md',
    '.py', '.js', '.java', '.go'
]

# Gamification
XP_LEVEL_MULTIPLIER = 100  # 100 XP = 1 level
```

**Note:** Git and webhook settings removed for MVP. Will be added in Phase 3 (see `spec/future/git-integrate.md`).

### 3.4 URL Configuration

**Update `synnovator/urls.py`:**

```python
from django.urls import path, include
from synnovator.hackathons import views as hackathon_views

urlpatterns = [
    # ... existing URLs ...

    # Hackathon-specific views (not handled by Wagtail pages)
    path('teams/create/', hackathon_views.create_team, name='create_team'),
    path('teams/<slug:slug>/join/', hackathon_views.join_team, name='join_team'),
    path('quests/<slug:slug>/submit/', hackathon_views.submit_quest, name='submit_quest'),

    # Wagtail handles HackathonPage URLs automatically
    # e.g., /hackathons/ai-challenge-2026/
]
```

**Note:** API and webhook endpoints will be added in Phase 3 (see `spec/future/git-integrate.md`).

---

