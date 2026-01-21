## Section 9: Critical Files

### 9.1 Files to Create (MVP - Phase 1)

#### Core Models
| File | Purpose | Lines (Est.) |
|------|---------|--------------|
| `synnovator/hackathons/models/hackathon.py` | HackathonPage, Phase (inline), Prize (inline) | 200 |
| `synnovator/hackathons/models/team.py` | Team, TeamMember | 120 |
| `synnovator/hackathons/models/quest.py` | Quest | 80 |
| `synnovator/hackathons/models/submission.py` | Submission (file upload + URL) | 120 |

**Note:** HackathonConfig and VerificationLog removed for MVP. Phase/Prize are inline models using ParentalKey.

#### Logic & Views
| File | Purpose | Lines (Est.) |
|------|---------|--------------|
| `synnovator/hackathons/views.py` | Team formation, quest submission views | 150 |
| `synnovator/hackathons/forms.py` | Submission forms, team creation forms | 100 |
| `synnovator/hackathons/scoring.py` | Score calculation and XP awarding | 80 |
| `synnovator/hackathons/matching.py` | Team matching algorithm (Phase 2) | 150 |

**Removed for MVP (defer to Phase 3):**
- ❌ `config_sync.py` - Git YAML parser
- ❌ `webhooks.py` - Webhook handlers
- ❌ `verification.py` - Verification engine
- See `spec/future/git-integrate.md` for Phase 3 implementation

#### Templates
| File | Purpose | Lines (Est.) |
|------|---------|--------------|
| `templates/pages/hackathon_page.html` | Hackathon detail page | 120 |
| `templates/pages/hackathon_listing_page.html` | Hackathon listing | 80 |
| `templates/pages/team_profile.html` | Team profile page | 150 |
| `templates/pages/team_formation.html` | Team formation page | 100 |
| `templates/pages/quest_listing.html` | Quest/Dojo listing | 100 |
| `templates/pages/quest_detail.html` | Quest detail + submission form | 120 |
| `templates/hackathons/submit_quest.html` | Quest submission form | 80 |
| `templates/components/hackathon/phase_timeline.html` | Timeline component | 50 |
| `templates/components/hackathon/leaderboard.html` | Leaderboard component | 80 |
| `templates/components/hackathon/team_card.html` | Team card component | 50 |

#### Admin & Wagtail Integration
| File | Purpose | Lines (Est.) |
|------|---------|--------------|
| `synnovator/hackathons/admin.py` | Wagtail ModelAdmin for Submission | 100 |
| `synnovator/hackathons/wagtail_hooks.py` | Admin menu items, custom CSS | 40 |

**Removed for MVP (defer to Phase 3):**
- ❌ Management commands (sync_hackathon_config.py, calculate_contributions.py)
- ❌ API files (serializers.py, api/views.py, api/urls.py)

#### Tests
| File | Purpose | Lines (Est.) |
|------|---------|--------------|
| `synnovator/hackathons/tests/test_models.py` | Model tests (Phase, Prize, Team, Submission) | 200 |
| `synnovator/hackathons/tests/test_views.py` | View tests (team formation, submission) | 150 |
| `synnovator/hackathons/tests/test_scoring.py` | Scoring and XP tests | 100 |
| `synnovator/hackathons/tests/test_matching.py` | Team matching tests (Phase 2) | 100 |

**Removed for MVP:**
- ❌ `test_config_sync.py`
- ❌ `test_webhooks.py`
- ❌ `test_verification.py`

### 9.2 Files to Modify

| File | Modifications | Priority |
|------|--------------|----------|
| `synnovator/users/models.py` | Add profile fields (preferred_role, bio, skills, xp_points, level, is_seeking_team) | High |
| `synnovator/settings/base.py` | Add hackathons to INSTALLED_APPS, add MVP config settings | High |
| `synnovator/urls.py` | Add hackathon routes (team creation, quest submission) | High |
| `templates/navigation/header.html` | Update nav: "Events" → "Hackathons", add "Dojo", "Teams" | Medium |
| `templates/navigation/footer.html` | Update footer links for hackathon platform | Medium |
| `templates/pages/home_page.html` | Replace blog CTAs with hackathon CTAs | Medium |
| `synnovator/search/models.py` | Index hackathons, teams, quests (Phase 2) | Low |

**Not needed for MVP:**
- ❌ `pyproject.toml` dependencies updates - no new backend dependencies required!

### 9.3 Files to Archive

**Move to `templates/_archived/`:**
- `templates/pages/article_page.html` (if keeping news app, repurpose for announcements)
- `templates/pages/news_listing_page.html` (if keeping news app, repurpose)
- `templates/components/card--article.html` (can reuse for announcements)

### 9.4 Files to Remove

**Delete these superseded templates:**
- `templates/pages/event_page.html` → Replaced by `hackathon_page.html`
- `templates/pages/event_listing_page.html` → Replaced by `hackathon_listing_page.html`
- `templates/pages/event_participants_page.html` → Replaced by `team_profile.html`

### 9.5 Summary Statistics

**MVP Files (Phase 1):**
- Models: 4 files (~520 lines)
- Logic: 4 files (~480 lines)
- Templates: 10 files (~930 lines)
- Admin: 2 files (~140 lines)
- Tests: 4 files (~550 lines)
- **Total: 24 files, ~2,620 lines of code**

**Files Deferred to Phase 3:**
- Git integration: 3 files (~450 lines)
- Webhook system: 2 files (~250 lines)
- API: 3 files (~380 lines)
- Management commands: 2 files (~140 lines)
- **Total deferred: 10 files, ~1,220 lines**

**Savings:** 32% fewer files, 32% less code to write for MVP!

### 9.6 Future Enhancements (Phase 3)

When adding Git integration and automated verification, create:

**File:** `spec/future/git-integrate.md`

This document will contain complete implementation guide for:
- `config_sync.py` - Git YAML parser and sync logic
- `webhooks.py` - HMAC-verified webhook endpoints
- `verification.py` - Automated verification engine
- `models/verification_log.py` - VerificationLog model for audit trails
- `api/` directory - REST API for integrations
- `management/commands/` - CLI commands for Git operations

See section 9.7 below for the outline.

### 9.7 Git Integration Files (Phase 3 Only)

**These files should NOT be created until Phase 3:**

| File | Purpose | When to Create |
|------|---------|----------------|
| `config_sync.py` | Git YAML parser | When platform has 100+ participants |
| `webhooks.py` | Webhook handlers with HMAC | When automated verification needed |
| `verification.py` | Verification engine | When manual review becomes bottleneck |
| `models/verification_log.py` | Audit trail for webhooks | Phase 3 |
| `api/serializers.py` | REST API | Phase 3 |
| `api/views.py` | API endpoints | Phase 3 |
| `management/commands/sync_hackathon_config.py` | Git sync CLI | Phase 3 |

**Reference:** See `spec/future/git-integrate.md` for complete implementation details.

---
