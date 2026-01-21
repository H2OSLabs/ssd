## Section 1: Data Structure Mapping

### 1.1 Page Model Transformations

| Old Structure | New Structure | Action | Rationale |
|--------------|---------------|--------|-----------|
| `ArticlePage` | `AnnouncementPage` | Keep/Rename | Platform updates and news still needed |
| `NewsListingPage` | `AnnouncementListingPage` | Keep/Rename | Landing page for announcements |
| `EventPage` | `HackathonPage` | Extend | Add phases (inline), prizes (inline), team config |
| `EventListingPage` | `HackathonListingPage` | Extend | Add filtering by status, phase |
| `EventParticipant` (if exists) | `TeamMember` | Transform | Enhance with contribution tracking |

### 1.2 New Model Entities

| Model | Purpose | Key Relationships |
|-------|---------|-------------------|
| `HackathonPage` | Wagtail page for hackathon details | Extends Page, has phases/prizes via ParentalKey |
| `Team` | Represents hackathon team | FK to HackathonPage, M2M to User |
| `TeamMember` | Through model for team membership | FK to Team and User |
| `Quest` | Dojo challenge | Can be standalone or hackathon-specific |
| `Submission` | File/URL submission | Polymorphic (quest or hackathon final) |
| `Phase` | Hackathon timeline phase | ParentalKey to HackathonPage (inline) |
| `Prize` | Award configuration | ParentalKey to HackathonPage (inline) |

**Note:** `HackathonConfig` removed - config stored directly on HackathonPage. `VerificationLog` simplified for manual verification (or deferred to Phase 3).

### 1.3 User Model Extensions

| Field | Type | Purpose |
|-------|------|---------|
| `preferred_role` | CharField | Hacker/Hipster/Hustler/Mentor (choices) |
| `bio` | TextField | User profile description |
| `skills` | JSONField | Skill tags for team matching |
| `xp_points` | IntegerField | Gamification points |
| `reputation_score` | DecimalField | Quality metric based on submissions |
| `level` | IntegerField | User level based on XP |
| `profile_completed` | BooleanField | Onboarding completion flag |
| `is_seeking_team` | BooleanField | Team formation indicator |

**Note:** Git-related fields (github_username, gitlab_username, oauth tokens) deferred to Phase 3 when Git integration is added.

### 1.4 Data Migration Mapping

| Source | Destination | Transformation Logic |
|--------|-------------|---------------------|
| `EventPage` (category='hackathon') | `HackathonPage` | Convert, set status='archived' |
| `EventPage` (other categories) | Keep as `EventPage` | No change (workshops, meetups) |
| `EventParticipant` records | `Team` + `TeamMember` | Group by team_name, preserve role |
| Existing `User` records | Extended `User` | Add fields with defaults, prompt profile completion |

---

