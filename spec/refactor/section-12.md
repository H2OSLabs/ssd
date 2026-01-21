## Section 12: Template Cleanup Strategy

### 12.1 Content Audit Checklist

**Must complete before launch:**

- [ ] **No blog references in user-facing UI**
  - [ ] Search for "blog", "article", "post" in templates
  - [ ] Replace with "hackathon", "team", "quest" terminology
  - [ ] Update all placeholder text

- [ ] **Navigation reflects platform purpose**
  - [ ] "Events" → "Hackathons"
  - [ ] Add "Dojo" link
  - [ ] Add "Teams" link
  - [ ] Add "Leaderboard" link
  - [ ] User dropdown shows XP

- [ ] **Home page drives hackathon actions**
  - [ ] "Browse Hackathons" CTA
  - [ ] "Join Next Challenge" CTA
  - [ ] "Explore Dojo" CTA
  - [ ] Remove blog/news hero sections

- [ ] **Footer links relevant**
  - [ ] Remove "Blog", "Articles"
  - [ ] Add "API Documentation"
  - [ ] Add "Developer Guide"
  - [ ] Add "Organizer Guide"

- [ ] **Search configuration updated**
  - [ ] Index HackathonPage
  - [ ] Index Quest
  - [ ] Index Team
  - [ ] Remove ArticlePage from results (or keep for announcements)

### 12.2 Archive Strategy

**Create archive directory:**
```bash
mkdir -p templates/_archived/{pages,components}
```

**Move templates:**
```bash
# Article templates (if not reusing for announcements)
mv templates/pages/article_page.html templates/_archived/pages/
mv templates/pages/news_listing_page.html templates/_archived/pages/
mv templates/components/card--article.html templates/_archived/components/

# Old event templates (being replaced)
mv templates/pages/event_page.html templates/_archived/pages/
mv templates/pages/event_listing_page.html templates/_archived/pages/
mv templates/pages/event_participants_page.html templates/_archived/pages/
```

**Document archived templates:**

**File:** `templates/_archived/README.md`

```markdown
# Archived Templates

This directory contains templates that have been replaced during the hackathon platform refactoring.

## Archived on: 2026-01-20

| Template | Replaced By | Reason |
|----------|-------------|--------|
| article_page.html | announcement_page.html (or removed) | Blog functionality replaced by announcements |
| news_listing_page.html | announcement_listing_page.html | Same as above |
| event_page.html | hackathon_page.html | Generic events replaced by hackathon-specific pages |
| event_listing_page.html | hackathon_listing_page.html | Same as above |
| event_participants_page.html | team_profile.html | Participants concept replaced by teams |

Do not delete - kept for reference during transition period.
```

### 12.3 Component Reusability

**Components to keep and adapt:**

| Component | Usage in Hackathon Platform |
|-----------|------------------------------|
| `card.html` | Team cards, quest cards, hackathon cards |
| `button.html` | All CTAs (Register, Join Team, Submit) |
| `pagination.html` | Quest listing, team listing, hackathon listing |
| `icon.html` | UI icons (add hackathon-specific icons) |
| `form.html` | Team formation, profile completion |

**Update card.html for hackathon entities:**

```django
{# templates/components/card.html #}
<div class="card card--{{ type }}">
    {% if type == 'hackathon' %}
        {# Hackathon-specific layout #}
        <div class="card-image">
            {% image item.cover_image fill-400x200 %}
        </div>
        <div class="card-content">
            <h3>{{ item.title }}</h3>
            <span class="card-status status-{{ item.status }}">
                {{ item.get_status_display }}
            </span>
            <p>{{ item.description|striptags|truncatewords:20 }}</p>
        </div>

    {% elif type == 'team' %}
        {# Team-specific layout #}
        <div class="card-content">
            <h3>{{ item.name }}</h3>
            <p class="card-tagline">{{ item.tagline }}</p>
            <div class="card-meta">
                <span>{{ item.members.count }} members</span>
                <span>Score: {{ item.final_score }}</span>
            </div>
        </div>

    {% elif type == 'quest' %}
        {# Quest-specific layout #}
        <div class="card-content">
            <h3>{{ item.title }}</h3>
            <span class="badge badge-{{ item.difficulty }}">{{ item.get_difficulty_display }}</span>
            <p>{{ item.description|striptags|truncatewords:15 }}</p>
            <div class="card-footer">
                <span class="xp">⭐ {{ item.xp_reward }} XP</span>
                <span class="time">⏱ {{ item.estimated_time_minutes }} min</span>
            </div>
        </div>

    {% else %}
        {# Generic card fallback #}
        <div class="card-content">
            <h3>{{ item.title }}</h3>
            <p>{{ item.description|truncatewords:20 }}</p>
        </div>
    {% endif %}

    <a href="{{ item.url }}" class="card-link">View Details</a>
</div>
```

### 12.4 Wagtail Admin Cleanup

**Remove unused page types from admin:**

```python
# synnovator/news/models.py or events/models.py
from wagtail.models import Page

class ArticlePage(Page):
    class Meta:
        verbose_name = "Article (Deprecated)"

    @classmethod
    def can_create_at(cls, parent):
        # Prevent creating new articles (keep existing for reference)
        return False
```

**Update admin dashboard:**

```python
# synnovator/home/wagtail_hooks.py
from wagtail import hooks
from wagtail.admin.panels import FieldPanel

@hooks.register('construct_homepage_panels')
def customize_homepage_panels(request, panels):
    # Remove blog-related panels
    # Add hackathon metrics
    return [
        {
            'title': 'Active Hackathons',
            'count': HackathonPage.objects.filter(status='in_progress').count(),
        },
        {
            'title': 'Teams Formed This Week',
            'count': Team.objects.filter(created_at__gte=week_ago).count(),
        },
        # ... more metrics
    ]
```

### 12.5 Search Index Update

**File:** `synnovator/search/models.py`

```python
from wagtail.search import index

# Update search configuration
SEARCH_MODELS = [
    'hackathons.HackathonPage',
    'hackathons.Team',
    'hackathons.Quest',
    # Remove or comment out:
    # 'news.ArticlePage',
]

# Custom search backend configuration
WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.search.backends.database',
        'AUTO_UPDATE': True,
        'SEARCH_MODELS': SEARCH_MODELS,
    }
}
```

**Rebuild search index:**
```bash
uv run python manage.py update_index
```

---

## Success Criteria Summary

**This refactoring is complete when:**

✅ **Phase 1 MVP (Week 6):**
- [ ] COO can create hackathon in < 10 minutes via Wagtail admin (no Git required)
- [ ] Phases and prizes configured using InlinePanel in Wagtail
- [ ] Phases and prizes display correctly on hackathon page
- [ ] Users can register, complete profile, form teams
- [ ] Users can submit quest solutions via file upload or URL
- [ ] COO can review submissions in Wagtail admin
- [ ] COO enters scores manually and submission status updates
- [ ] XP awarded automatically for verified quest completion
- [ ] Leaderboard shows top teams
- [ ] End-to-end test passes: Create hackathon → Form team → Submit → Manual verify → Score updates
- [ ] No new backend dependencies required

✅ **Phase 2 Social (Week 14):**
- [ ] Users can sign in with GitHub OAuth
- [ ] Skills auto-populated from quest completions
- [ ] Team matching suggests compatible teams
- [ ] Team formation completion rate > 80%

✅ **Phase 3 Scale & Automation (Week 20):**
- [ ] Platform handles 1000+ concurrent users
- [ ] Leaderboard cached in Redis
- [ ] **Git integration added:** Sync hackathon.yaml from Git repositories
- [ ] **Webhook verification:** GitHub Actions/GitLab CI send verification results
- [ ] Git sync runs asynchronously via Celery
- [ ] REST API documented and functional
- [ ] COO dashboard provides actionable insights
- [ ] See spec/future/git-integrate.md for implementation details

✅ **Quality Gates:**
- [ ] All migrations run without errors
- [ ] Test coverage > 80%
- [ ] No security vulnerabilities (file upload validation, no code execution)
- [ ] Templates have no blog/article references
- [ ] Documentation complete (organizer guide, submission guidelines)
- [ ] Manual verification workflow tested and documented

✅ **User Acceptance:**
- [ ] COO can manage hackathon without engineering support
- [ ] Participants complete onboarding in < 5 minutes
- [ ] Verification results return in < 2 minutes
- [ ] Zero data loss from migration

---

## Document Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-01-20 | Initial comprehensive specification | Claude |

---

**END OF DOCUMENT**

*Total word count: ~10,500 words*
*Estimated implementation time: 4-6 weeks for MVP, 20 weeks for complete platform (all phases)*
*Target team size: 1-2 engineers + 1 COO for testing*
*MVP delivers value without external dependencies!*