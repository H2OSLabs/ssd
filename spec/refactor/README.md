# Synnovator Hackathon Platform Refactoring Specification

This directory contains the detailed refactoring specification for transforming the Wagtail news template into a full-featured AI hackathon platform.

## Quick Navigation

**Start here:** [Overview](./overview.md) - Complete document index and quick start guide

## Document Sections

| Section | File | Description | Size |
|---------|------|-------------|------|
| **Overview** | [overview.md](./overview.md) | Document index, quick start, success criteria | 6.6KB |
| **Section 1** | [section-01.md](./section-01.md) | Data Structure Mapping | 2.4KB |
| **Section 2** | [section-02.md](./section-02.md) | Database Schema Design | 27KB |
| **Section 3** | [section-03.md](./section-03.md) | App Structure & Organization | 3.6KB |
| **Section 4** | [section-04.md](./section-04.md) | Template Refactoring Strategy | 18KB |
| **Section 5** | [section-05.md](./section-05.md) | Wagtail CMS Configuration (MVP) | 14KB |
| **Section 6** | [section-06.md](./section-06.md) | Manual Verification System (MVP) | 10KB |
| **Section 7** | [section-07.md](./section-07.md) | Migration Strategy | 8.1KB |
| **Section 8** | [section-08.md](./section-08.md) | Implementation Phases | 3.2KB |
| **Section 9** | [section-09.md](./section-09.md) | Critical Files | 3.8KB |
| **Section 10** | [section-10.md](./section-10.md) | Security Considerations | 5.8KB |
| **Section 11** | [section-11.md](./section-11.md) | Technology Additions | 2.1KB |
| **Section 12** | [section-12.md](./section-12.md) | Template Cleanup Strategy | 8.2KB |

**Total:** ~112KB of documentation

## Document Structure

Each section is self-contained and can be read independently, but sections reference each other where appropriate.

### For Implementation Teams

**If you're implementing the refactoring, read in this order:**

1. [Overview](./overview.md) - Understand the big picture
2. [Section 1: Data Structure Mapping](./section-01.md) - What's changing
3. [Section 8: Implementation Phases](./section-08.md) - The roadmap (MVP in 4-6 weeks)
4. [Section 2: Database Schema](./section-02.md) - Core models (no Git fields in MVP)
5. [Section 5: Wagtail CMS Configuration](./section-05.md) - MVP configuration approach
6. [Section 6: Manual Verification](./section-06.md) - MVP verification workflow
7. [Section 9: Critical Files](./section-09.md) - 32% code reduction for MVP
8. Continue with remaining sections as needed

### For Project Managers

**Focus on these sections:**

- [Overview](./overview.md) - Success criteria and timeline
- [Section 8: Implementation Phases](./section-08.md) - Week-by-week plan
- [Section 9: Critical Files](./section-09.md) - Scope of work

### For Security Reviewers

**Review these sections:**

- [Section 10: Security Considerations](./section-10.md) - File upload security, access control
- [Section 6: Manual Verification](./section-06.md) - Manual review workflow
- [Section 5: Wagtail CMS Configuration](./section-05.md) - CMS security patterns
- **Note:** Webhook/Git security deferred to Phase 3 (see spec/future/git-integrate.md)

### For Frontend Developers

**Focus on these sections:**

- [Section 4: Template Refactoring](./section-04.md) - All UI templates
- [Section 12: Template Cleanup](./section-12.md) - What to remove
- [Section 11: Technology Additions](./section-11.md) - Frontend dependencies

## Key Concepts

### Wagtail-Native MVP (Phase 1)
All hackathon configurations stored directly in Wagtail CMS:
- InlinePanel for phases and prizes (no separate config model)
- Manual verification via Wagtail admin interface
- File upload or URL submission (no Git integration required)
- Zero new backend dependencies
- Faster delivery: 4-6 weeks instead of 20 weeks

### Zero Code Execution
The platform NEVER executes user-submitted code. Security principles:
- Submissions via file upload or public repository URL
- Manual review by COO/judges in safe environment
- XP awarded automatically after score entry
- File upload validation (size limits, type whitelisting)

### Future: Automated Verification (Phase 3)
When platform reaches 100+ participants per event:
- Git integration for configuration versioning
- Webhook-driven verification from CI/CD systems
- HMAC signature verification for score submissions
- See **spec/future/git-integrate.md** for implementation guide

## Implementation Timeline

- **Phase 1 MVP (Week 3-6):** Core platform with Wagtail CMS + manual verification
  - No Git integration, no webhooks, no external dependencies
  - Delivers value immediately for < 100 participants
- **Phase 2 Social (Week 7-12):** OAuth, team matching, skill verification
- **Phase 3 Scale (Week 13-20):** Git integration, automated webhooks, gamification
  - See **spec/future/git-integrate.md** for Phase 3 implementation

**Total:** 4-6 weeks for MVP, 20 weeks for complete platform
**Team size:** 1-2 engineers + 1 COO for testing

## Technologies

### Backend (MVP - Phase 1)
- Python 3.12
- Django + Wagtail CMS
- PostgreSQL (or SQLite for development)
- **NO new dependencies required!**

### Backend (Phase 3 Additions)
- PyYAML (Git YAML parsing)
- requests (Git API calls)
- GitPython (Git operations)
- cryptography (webhook HMAC)
- Celery + Redis (async tasks)
- DRF (REST API)

### Frontend (All Phases)
- Tailwind CSS (already present)
- Alpine.js (interactive components)
- Chart.js (leaderboards)
- Webpack (asset pipeline)

### Integration (Phase 3 Only)
- GitHub Actions (automated verification)
- GitLab CI (alternative verification)
- REST API (external integrations)

## Success Metrics

**Phase 1 MVP:**
- COO creates hackathon in < 10 minutes using Wagtail admin (no Git knowledge required)
- COO reviews and scores submission in < 5 minutes
- User completes onboarding in < 5 minutes
- End-to-end test: Create → Form team → Submit → Manual verify → Score updates
- Zero new backend dependencies
- Works for < 100 participants per event

**Phase 2 Social:**
- Team formation completion rate > 80%
- GitHub OAuth integration functional
- Skill-based team matching reduces formation time by 50%

**Phase 3 Scale:**
- Platform handles 1000+ concurrent users
- Leaderboard response time < 100ms (Redis caching)
- Automated webhook verification operational
- Git sync functional for configuration versioning

## Related Documentation

- **Product Requirements:** [../hackathon-prd.md](../hackathon-prd.md)
- **Original Implementation Notes:** [../events_implementation_guide.md](../events_implementation_guide.md)
- **Consolidated Document:** [../refactor-for-hackathon.md](../refactor-for-hackathon.md)
- **Future Phase 3:** [../future/git-integrate.md](../future/git-integrate.md) - Git integration implementation guide

## Contributing

When updating this specification:

1. Update the relevant section file
2. Update the consolidated document if maintaining it
3. Increment version in overview.md
4. Document changes in revision history

## Questions?

For clarifications or suggestions:
- Create an issue in the project repository
- Contact the engineering team
- Refer to inline comments in section files

---

**Ready to start? → [Overview](./overview.md)**
