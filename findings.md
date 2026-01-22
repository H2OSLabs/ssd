# Findings & Decisions

## Requirements
- Add pytest testing framework with pytest-django
- Create testing skill for wagtail-builder (rules/test.md)
- Prioritize backend Wagtail CMS model tests
- Add template integration tests to verify model-template sync
- Run coverage and fill gaps

## Research Findings

### Existing Test Structure
- `synnovator/search/tests/test_view.py` - Django TestCase (3 tests)
- `synnovator/utils/tests/test_i18n.py` - Comprehensive i18n tests (~20 tests)
- `synnovator/hackathons/tests/` - Empty (only `__init__.py`)
- `synnovator/community/tests.py` - Empty placeholder
- `synnovator/notifications/tests.py` - Empty placeholder

### Core Models to Test

**Hackathons App**:
| Model | Type | Priority | Dependencies |
|-------|------|----------|--------------|
| HackathonIndexPage | Wagtail Page | High | BasePage |
| HackathonPage | Wagtail Page | High | Phase, Prize, Quest |
| Phase | InlineModel | High | HackathonPage |
| Prize | InlineModel | Medium | HackathonPage |
| Quest | Snippet | High | TranslatableMixin |
| Team | Django Model | High | User, HackathonPage |
| TeamMember | Through Model | High | Team, User |
| Submission | Django Model | High | User/Team, Quest/Hackathon |
| HackathonRegistration | Snippet | Medium | User, HackathonPage |
| CompetitionRule | Snippet | Medium | HackathonPage |
| RuleViolation | Django Model | Medium | Team, CompetitionRule |
| JudgeScore | Snippet | Medium | Submission, User |
| ScoreBreakdown | Snippet | Medium | HackathonPage |
| AdvancementLog | Django Model | Medium | Team, HackathonPage |

**Users App**:
| Model | Type | Priority |
|-------|------|----------|
| User | Custom AbstractUser | High |

**Community App**:
| Model | Type | Priority |
|-------|------|----------|
| CommunityPost | Snippet | Medium |
| Comment | Django Model | Medium |
| Like | Django Model | Medium |
| UserFollow | Django Model | Medium |
| Report | Snippet | Low |

**Notifications App**:
| Model | Type | Priority |
|-------|------|----------|
| Notification | Django Model | Medium |

**News App**:
| Model | Type | Priority |
|-------|------|----------|
| ArticlePage | Wagtail Page | Medium |
| NewsIndexPage | Wagtail Page | Medium |

### Template-Model Dependencies
Templates that need sync tests when models change:

| Template | Models Used |
|----------|-------------|
| hackathon_index_page.html | HackathonIndexPage, HackathonPage |
| hackathon_page.html | HackathonPage, Phase, Prize, Team |
| quest_detail_page.html | Quest |
| quest_list_page.html | Quest |
| team_detail_page.html | Team, TeamMember, User |
| user_profile_page.html | User |
| article_page.html | ArticlePage, AuthorSnippet |
| news_listing_page.html | NewsIndexPage, ArticlePage |

## Technical Decisions

| Decision | Rationale |
|----------|-----------|
| pytest + pytest-django | Better fixtures, cleaner assertions, parallel support |
| factory_boy | Declarative test data, handles relationships |
| pytest-cov | Industry standard coverage tool |
| Separate conftest.py per app | Isolated fixtures, easier maintenance |
| Template rendering tests | Catch template-model sync issues early |

## Issues Encountered

| Issue | Resolution |
|-------|------------|

## Resources
- pytest-django docs: https://pytest-django.readthedocs.io/
- factory_boy docs: https://factoryboy.readthedocs.io/
- wagtail testing docs: https://docs.wagtail.org/en/stable/advanced_topics/testing.html
- Project wagtail-builder skill: .claude/skills/wagtail-builder/

## Visual/Browser Findings
N/A - This is a backend testing task

---
*Update this file after every 2 view/browser/search operations*
*This prevents visual information from being lost*
