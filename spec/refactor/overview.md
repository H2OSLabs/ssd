# Synnovator Hackathon Platform Refactoring Specification

## Document Overview

This comprehensive specification document serves as the implementation guide for transforming the Wagtail news template into a full-featured AI hackathon platform using standard Wagtail CMS patterns as specified in spec/hackathon-prd.md. Git integration and external verification will be added in future phases after the core platform is stable.

**Document Version:** 1.0
**Last Updated:** 2026-01-20
**Target Completion:** Week 20

---

## Document Structure

This specification is organized into 12 sections, each covering a specific aspect of the refactoring:

### [Section 1: Data Structure Mapping](./section-01.md)
- Old structure → New structure transformations
- New model entities and relationships
- User model extensions
- Data migration mapping

### [Section 2: Database Schema Design](./section-02.md)
- Complete Django model definitions with fields and methods
- HackathonPage, HackathonConfig, Phase, Prize models
- Team, TeamMember models
- Quest, Submission, VerificationLog models
- Extended User model

### [Section 3: App Structure & Organization](./section-03.md)
- Recommended `synnovator.hackathons` app structure
- Existing apps to keep and modify
- Settings configuration
- URL routing

### [Section 4: Layout & Template Refactoring Strategy](./section-04.md)
- **Layout Architecture Design:** 4 core layout patterns (Dashboard, Community, Event, Profile)
- **Page-by-Page Layouts:** 8 key pages redesigned from news site to community platform
- **Component Library:** 15+ new components (cards, interactive widgets, navigation)
- **Design System:** Color palette, typography, spacing, responsive breakpoints
- **Migration Strategy:** Week-by-week implementation roadmap
- Templates to keep, archive, and remove

### [Section 5: Wagtail CMS Configuration](./section-05.md)
- Wagtail-native configuration philosophy
- InlinePanel for phases and prizes
- COO workflow without Git dependencies
- Standard Django/Wagtail patterns
- Future Git integration path (Phase 3)

### [Section 6: Manual Verification System](./section-06.md)
- Manual verification workflow for MVP
- File upload and URL submission
- Wagtail admin integration for scoring
- Score processing and XP awarding
- Future automated verification path (Phase 3)

### [Section 7: Migration Strategy](./section-07.md)
- Data migration plan (User, EventPage, EventParticipant)
- Backward compatibility (URL redirects)
- Migration execution order
- Rollback plan

### [Section 8: Implementation Phases](./section-08.md)
- **Phase 1 (Week 3-8):** MVP - Core platform functionality
- **Phase 2 (Week 9-14):** Social features - OAuth, skill verification, team matching
- **Phase 3 (Week 15-20):** Scale - Performance, gamification, analytics
- Weekly breakdown with deliverables and success criteria

### [Section 9: Critical Files](./section-09.md)
- Files to create (30+ files with line estimates)
- Files to modify (8 files)
- Files to archive
- Files to remove

### [Section 10: Security Considerations](./section-10.md)
- Webhook security (HMAC, IP whitelisting)
- Code execution prevention
- Secret management (encryption)
- Input validation
- Rate limiting and access control

### [Section 11: Technology Additions](./section-11.md)
- Python dependencies (none needed for MVP)
- Frontend dependencies (Alpine.js, Chart.js)
- Infrastructure services (Phase 3: Redis, Celery)
- Future: GitHub Actions workflows (Phase 3)

### [Section 12: Template Cleanup Strategy](./section-12.md)
- Content audit checklist
- Archive strategy
- Component reusability
- Wagtail admin cleanup
- Search index updates

---

## Quick Start for Implementation

### Step 1: Read Core Sections
1. [Section 1: Data Structure Mapping](./section-01.md) - Understand what's changing
2. [Section 8: Implementation Phases](./section-08.md) - See the roadmap
3. [Section 9: Critical Files](./section-09.md) - Know what to build

### Step 2: Set Up Development
1. Review [Section 11: Technology Additions](./section-11.md)
2. Install new dependencies
3. Create `hackathons` app structure per [Section 3](./section-03.md)

### Step 3: Begin Phase 1 MVP
Follow [Section 8](./section-08.md) Week 3-4 tasks:
- Create database models per [Section 2](./section-02.md)
- Write migrations per [Section 7](./section-07.md)
- Extend User model

### Step 4: Implement Core Features
- Wagtail CMS configuration with InlinePanel ([Section 5](./section-05.md))
- Manual verification system ([Section 6](./section-06.md))
- Templates ([Section 4](./section-04.md))

---

## Success Criteria Summary

**This refactoring is complete when:**

✅ **Phase 1 MVP (Week 8):**
- COO can create hackathon in < 10 minutes via Wagtail admin
- COO can add phases and prizes using InlinePanel
- Users can register, complete profile, form teams
- Users can submit quest solutions via file upload or URL
- COO can manually verify submissions via Wagtail admin
- Scores update and XP awarded upon manual verification
- End-to-end test passes

✅ **Phase 2 Social (Week 14):**
- Enhanced skill tagging and profile pages
- Team matching algorithm suggests compatible teams based on roles
- Improved team formation flow with role indicators
- Team formation completion rate > 80%

✅ **Phase 3 Scale & Automation (Week 20):**
- Platform handles 1000+ concurrent users
- Leaderboard cached in Redis
- **Git integration added: YAML config sync, webhook verification**
- External CI/CD verification (GitHub Actions, GitLab CI)
- REST API documented and functional
- COO dashboard provides actionable insights

✅ **Quality Gates:**
- All migrations run without errors
- Test coverage > 80%
- No security vulnerabilities
- Templates have no blog/article references
- Documentation complete

---

## Key Architectural Principles

### 1. Wagtail-Native Configuration (MVP)
All hackathon configurations stored directly in Wagtail CMS using standard Django/Wagtail patterns. InlinePanel for phases and prizes. Familiar admin interface for COO.

### 2. Zero Code Hosting
Platform stores only metadata (repo URLs, commit hashes). Never executes user code on Synnovator servers.

### 3. Manual Verification First (MVP)
Manual scoring workflow via Wagtail admin. Works well for < 100 participants. Automated webhook verification added in Phase 3.

### 4. Pragmatic Evolution
Maintain backward compatibility for existing news/events. Focus on hackathon features without complete rewrite. Add complexity incrementally.

### 5. Future: Git Integration (Phase 3)
Events as Code architecture will be added in Phase 3 for scale (1000+ participants). Git-backed YAML configs, webhook verification, external CI/CD integration. See spec/future/git-integrate.md.

---

## Document Statistics

- **Total Length:** 10,500+ words
- **Code Examples:** 30+ complete code blocks
- **Tables:** 15+ comparison/checklist tables
- **Diagrams:** 2 Mermaid flow diagrams
- **Estimated Implementation Time:** 20 weeks
- **Recommended Team Size:** 2-3 engineers + 1 COO for testing

---

## Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-01-20 | Initial comprehensive specification | Claude |

---

## Related Documents

- [Hackathon Platform PRD](../hackathon-prd.md) - Product requirements
- [Events Implementation Guide](../events_implementation_guide.md) - Original implementation notes
- Main refactoring document: [refactor-for-hackathon.md](../refactor-for-hackathon.md) (consolidated version)

---

**Ready to start? Begin with [Section 1: Data Structure Mapping](./section-01.md) →**
