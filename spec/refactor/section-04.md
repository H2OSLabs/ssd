## Section 4: Layout & Template Refactoring Strategy

### 4.1 Overview: From News Site to Community Platform

**Current Problem**: The existing template is optimized for a **news/blog site**:
- Single-column, linear content flow
- Chronological organization
- Reader-focused (browse, read, leave)
- Author-centric metadata
- Minimal interactivity

**Target**: Transform into a **community-driven hackathon platform**:
- Multi-dimensional navigation (events, teams, participants, projects)
- Social interaction and team formation
- Action-oriented (join, submit, compete)
- Profile and reputation systems
- Real-time status updates
- Dashboard and grid layouts

### 4.2 Core Layout Patterns

#### 4.2.1 Dashboard Layout
**Use cases**: User dashboard, COO operations panel, team management

**Structure**:
```
[Sidebar (20-25% width, sticky)]        [Main Content (75-80% width)]
- Navigation menu                       - Content area
- Quick actions                         - Contextual panels
- Profile snippet                       - Activity feed
- Current event status
```

**Implementation**: `templates/layouts/dashboard_layout.html`

**Example Code**:
```django
{% extends "base.html" %}

{% block content %}
<div class="dashboard-layout">
    <aside class="dashboard-sidebar">
        {% block sidebar %}
        <nav class="sidebar-nav">
            <ul>
                <li><a href="{% url 'dashboard:home' %}">Dashboard</a></li>
                <li><a href="{% url 'dashboard:teams' %}">My Teams</a></li>
                <li><a href="{% url 'dashboard:submissions' %}">Submissions</a></li>
                <li><a href="{% url 'dashboard:settings' %}">Settings</a></li>
            </ul>
        </nav>

        <div class="sidebar-profile">
            <div class="profile-avatar">{{ user.get_initials }}</div>
            <div class="profile-info">
                <div class="profile-name">{{ user.get_full_name }}</div>
                <div class="profile-xp">Level {{ user.level }} • {{ user.xp_points }} XP</div>
            </div>
        </div>
        {% endblock sidebar %}
    </aside>

    <main class="dashboard-main">
        {% block dashboard_content %}{% endblock %}
    </main>
</div>
{% endblock content %}
```

#### 4.2.2 Community Layout
**Use cases**: Team browsing, participant directory, project showcase

**Structure**:
```
[Filter Sidebar (25% width)]            [Grid Content (75% width)]
- Search box                            - Card grid (2-3 columns)
- Filters (skills, roles, status)       - Pagination
- Quick stats
```

**Implementation**: `templates/layouts/community_layout.html`

**Example Code**:
```django
{% extends "base.html" %}

{% block content %}
<div class="community-layout">
    <aside class="filter-sidebar">
        {% block filters %}
        <div class="filter-section">
            <h3>Search</h3>
            <input type="search" name="q" placeholder="Search..." class="filter-search">
        </div>

        <div class="filter-section">
            <h3>Filters</h3>
            {% block filter_options %}{% endblock %}
        </div>

        <div class="filter-section">
            <h3>Quick Stats</h3>
            {% block quick_stats %}{% endblock %}
        </div>
        {% endblock filters %}
    </aside>

    <main class="community-main">
        {% block community_content %}
        <div class="content-grid">
            {% block grid_items %}{% endblock %}
        </div>

        {% block pagination %}{% endblock %}
        {% endblock community_content %}
    </main>
</div>
{% endblock content %}
```

#### 4.2.3 Event Layout
**Use cases**: Hackathon detail pages

**Structure**:
```
[Event Header - Full width]
- Cover image hero
- Title, status, countdown
- Quick actions (Register, Join Team)

[Tab Navigation]
- Overview | Teams | Projects | Rules | Leaderboard

[Tab Content: Main (70%) + Sidebar (30%)]
Main: Tab-specific content
Sidebar (sticky): Event stats, team formation widget, current phase
```

**Implementation**: `templates/layouts/event_layout.html`

**Example Code**:
```django
{% extends "base.html" %}

{% block content %}
<article class="event-layout">
    <header class="event-header">
        {% block event_header %}
        {% if page.cover_image %}
            {% image page.cover_image fill-1200x400 as cover %}
            <img src="{{ cover.url }}" alt="{{ page.title }}" class="cover-image">
        {% endif %}

        <div class="event-header-content">
            <h1 class="event-title">{{ page.title }}</h1>
            <div class="event-meta">
                <span class="status-badge status-{{ page.status }}">
                    {{ page.get_status_display }}
                </span>
                {% include "components/countdown-timer.html" with end_date=page.get_current_phase.end_date %}
            </div>
            <div class="event-actions">
                {% block event_actions %}{% endblock %}
            </div>
        </div>
        {% endblock event_header %}
    </header>

    <div class="event-tabs" x-data="{ activeTab: 'overview' }">
        <nav class="tab-navigation">
            <button @click="activeTab = 'overview'" :class="{ active: activeTab === 'overview' }">
                Overview
            </button>
            <button @click="activeTab = 'teams'" :class="{ active: activeTab === 'teams' }">
                Teams
            </button>
            <button @click="activeTab = 'projects'" :class="{ active: activeTab === 'projects' }">
                Projects
            </button>
            <button @click="activeTab = 'rules'" :class="{ active: activeTab === 'rules' }">
                Rules
            </button>
            <button @click="activeTab = 'leaderboard'" :class="{ active: activeTab === 'leaderboard' }">
                Leaderboard
            </button>
        </nav>

        <div class="event-content-wrapper">
            <main class="event-main">
                <div x-show="activeTab === 'overview'" x-transition>
                    {% block tab_overview %}{% endblock %}
                </div>
                <div x-show="activeTab === 'teams'" x-transition>
                    {% block tab_teams %}{% endblock %}
                </div>
                <div x-show="activeTab === 'projects'" x-transition>
                    {% block tab_projects %}{% endblock %}
                </div>
                <div x-show="activeTab === 'rules'" x-transition>
                    {% block tab_rules %}{% endblock %}
                </div>
                <div x-show="activeTab === 'leaderboard'" x-transition>
                    {% block tab_leaderboard %}{% endblock %}
                </div>
            </main>

            <aside class="event-sidebar">
                {% block event_sidebar %}
                <div class="sidebar-section">
                    <h3>Event Stats</h3>
                    {% include "components/stats-panel.html" %}
                </div>

                <div class="sidebar-section">
                    <h3>Current Phase</h3>
                    {% include "components/phase-indicator.html" with phase=page.get_current_phase %}
                </div>

                {% if user.is_authenticated and not user.has_team_in_hackathon %}
                <div class="sidebar-section">
                    <h3>Looking for teammates?</h3>
                    {% include "components/team-formation-widget.html" %}
                </div>
                {% endif %}
                {% endblock event_sidebar %}
            </aside>
        </div>
    </div>
</article>
{% endblock content %}
```

#### 4.2.4 Profile Layout
**Use cases**: User profiles, team profiles

**Structure**:
```
[Profile Header - Full width]
- Avatar/logo (large)
- Name, tagline
- Key metrics (XP, reputation, team count)
- Action buttons

[Tab Content: Main (70%) + Sidebar (30%)]
Main: About | Skills | Projects | History
Sidebar: Badges, achievements, recent activity
```

**Implementation**: `templates/layouts/profile_layout.html`

**Example Code**:
```django
{% extends "base.html" %}

{% block content %}
<article class="profile-layout">
    <header class="profile-header">
        {% block profile_header %}
        <div class="profile-avatar-large">
            {% if profile.avatar %}
                <img src="{{ profile.avatar.url }}" alt="{{ profile.name }}">
            {% else %}
                <span class="avatar-placeholder">{{ profile.get_initials }}</span>
            {% endif %}
        </div>

        <div class="profile-header-content">
            <h1 class="profile-name">{{ profile.name }}</h1>
            {% block profile_tagline %}{% endblock %}

            <div class="profile-metrics">
                {% block profile_metrics %}{% endblock %}
            </div>

            <div class="profile-actions">
                {% block profile_actions %}{% endblock %}
            </div>
        </div>
        {% endblock profile_header %}
    </header>

    <div class="profile-tabs" x-data="{ activeTab: 'about' }">
        <nav class="tab-navigation">
            {% block tab_navigation %}
            <button @click="activeTab = 'about'" :class="{ active: activeTab === 'about' }">
                About
            </button>
            <button @click="activeTab = 'skills'" :class="{ active: activeTab === 'skills' }">
                Skills
            </button>
            <button @click="activeTab = 'projects'" :class="{ active: activeTab === 'projects' }">
                Projects
            </button>
            <button @click="activeTab = 'history'" :class="{ active: activeTab === 'history' }">
                History
            </button>
            {% endblock tab_navigation %}
        </nav>

        <div class="profile-content-wrapper">
            <main class="profile-main">
                <div x-show="activeTab === 'about'" x-transition>
                    {% block tab_about %}{% endblock %}
                </div>
                <div x-show="activeTab === 'skills'" x-transition>
                    {% block tab_skills %}{% endblock %}
                </div>
                <div x-show="activeTab === 'projects'" x-transition>
                    {% block tab_projects %}{% endblock %}
                </div>
                <div x-show="activeTab === 'history'" x-transition>
                    {% block tab_history %}{% endblock %}
                </div>
            </main>

            <aside class="profile-sidebar">
                {% block profile_sidebar %}
                <div class="sidebar-section">
                    <h3>Badges</h3>
                    {% block badges %}{% endblock %}
                </div>

                <div class="sidebar-section">
                    <h3>Recent Activity</h3>
                    {% block recent_activity %}{% endblock %}
                </div>
                {% endblock profile_sidebar %}
            </aside>
        </div>
    </div>
</article>
{% endblock content %}
```

### 4.3 Page-by-Page Layout Design

#### 4.3.1 Home Page (Platform Landing)
**Current**: Blog hero + featured articles carousel
**New**: Community dashboard

**Layout Structure**:
```markdown
1. [Hero Section - Full width]
   - Platform tagline
   - 3 CTAs: "Browse Hackathons" | "Explore Dojo" | "Find Your Team"

2. [Stats Bar - Full width]
   - Active Hackathons: 12 | Teams Formed: 347 | Quests Completed: 8,429

3. [Featured Hackathons - 3-column grid]
   - Event cards with countdown timers and status badges

4. [Dojo Preview - 2-column split]
   - Left: Quest of the Day (featured challenge)
   - Right: Top Questers This Week (leaderboard preview)

5. [Team Formation Widget - Full width]
   - "Looking for teammates?" CTA
   - Role-based team recommendations
```

**Template**: `templates/pages/home_page.html`

#### 4.3.2 Hackathon Listing Page
**Current**: Single-column article listing
**New**: Filtered grid layout

**Layout Structure**:
```markdown
[Header Section]
- Title: "Hackathons"
- Quick stats (Active: 5, Upcoming: 8, Completed: 23)

[Two-column layout]
  [Left: Filter Sidebar - 25%]
  - Search
  - Status: Active, Upcoming, Registration, Completed
  - Date range picker
  - Team size filter
  - Difficulty filter

  [Right: Event Grid - 75%]
  - 2-3 column responsive grid
  - Event cards (cover, title, dates, team count, status)
  - Pagination
```

**Template**: `templates/pages/hackathon_listing_page.html`

#### 4.3.3 Hackathon Detail Page
**Current**: Article-style single-column
**New**: Event dashboard with tabs

**Layout Structure**:
```markdown
[Event Header - Full width hero]
- Cover image
- Title (large serif)
- Status badge + Phase indicator
- Countdown timer
- Actions: [Register] [Join Team] [Submit Project]

[Tab Navigation]
- Overview | Teams | Projects | Rules | Leaderboard

[Content Layout: Main (70%) + Sidebar (30%)]
  [Main Content]
  - Tab-specific content (description, team grid, project gallery, etc.)

  [Sidebar - Sticky]
  - Event Stats (Teams: 47, Participants: 234, Submissions: 189)
  - Current Phase ("Hacking Phase" - Ends in 3d 12h)
  - Team Formation Widget ("Looking for teammates?")
```

**Template**: `templates/pages/hackathon_page.html`

**Example Code**:
```django
{% extends "layouts/event_layout.html" %}
{% load wagtailcore_tags wagtailimages_tags %}

{% block event_actions %}
{% if page.status == 'registration_open' %}
    <a href="{% url 'hackathons:register' page.slug %}" class="btn btn-primary btn-lg">
        Register Now
    </a>
{% elif page.status == 'in_progress' and user.is_authenticated %}
    <a href="{% url 'hackathons:teams' page.slug %}" class="btn btn-primary">
        View Teams
    </a>
    <a href="{% url 'hackathons:submit' page.slug %}" class="btn btn-secondary">
        Submit Project
    </a>
{% endif %}
{% endblock %}

{% block tab_overview %}
<div class="hackathon-overview">
    {{ page.description|richtext }}

    {% if page.body %}
        {% include_block page.body %}
    {% endif %}

    {# Phase Timeline #}
    {% if page.phases.exists %}
        <section class="phases-section">
            <h2>Event Timeline</h2>
            {% include "components/phase-timeline.html" with phases=page.phases.all %}
        </section>
    {% endif %}

    {# Prizes Section #}
    {% if page.prizes.exists %}
        <section class="prizes-section">
            <h2>Prizes</h2>
            <div class="prizes-grid">
                {% for prize in page.prizes.all %}
                    {% include "components/prize-card.html" with prize=prize %}
                {% endfor %}
            </div>
        </section>
    {% endif %}
</div>
{% endblock %}

{% block tab_teams %}
<div class="teams-grid">
    {% for team in page.teams.all %}
        {% include "components/team-card.html" with team=team %}
    {% empty %}
        <p class="no-teams">No teams have formed yet. Be the first!</p>
    {% endfor %}
</div>
{% endblock %}

{% block tab_leaderboard %}
{% include "components/leaderboard.html" with teams=page.get_leaderboard %}
{% endblock %}

{% block event_sidebar %}
{{ block.super }}
{% if page.phases.exists %}
<div class="sidebar-section">
    <h3>Event Timeline</h3>
    <ul class="phase-list-compact">
        {% for phase in page.phases.all %}
        <li class="{% if phase.is_active %}active{% endif %}">
            <strong>{{ phase.title }}</strong>
            <span class="phase-dates">{{ phase.start_date|date:"M d" }} - {{ phase.end_date|date:"M d" }}</span>
        </li>
        {% endfor %}
    </ul>
</div>
{% endif %}
{% endblock %}
```

#### 4.3.4 Team Profile Page
**Template**: `templates/pages/team_profile.html`

**Example Code**:
```django
{% extends "layouts/profile_layout.html" %}
{% load static %}

{% block profile_tagline %}
{% if team.tagline %}
    <p class="profile-tagline">{{ team.tagline }}</p>
{% endif %}
<div class="team-hackathon">
    <a href="{{ team.hackathon.url }}">{{ team.hackathon.title }}</a>
</div>
{% endblock %}

{% block profile_metrics %}
<div class="metric">
    <span class="metric-value">{{ team.members.count }}</span>
    <span class="metric-label">Members</span>
</div>
<div class="metric">
    <span class="metric-value">{{ team.final_score|default:"—" }}</span>
    <span class="metric-label">Score</span>
</div>
<div class="metric">
    <span class="metric-value">{{ team.rank|default:"—" }}</span>
    <span class="metric-label">Rank</span>
</div>
<div class="metric">
    <span class="status-badge status-{{ team.status }}">
        {{ team.get_status_display }}
    </span>
</div>
{% endblock %}

{% block profile_actions %}
{% if user.is_authenticated and not user in team.members.all %}
    {% if team.status == 'looking_for_members' %}
    <button class="btn btn-primary" onclick="applyToTeam()">Apply to Join</button>
    {% endif %}
{% elif user in team.members.all %}
    <a href="{% url 'hackathons:team_manage' team.hackathon.slug team.slug %}" class="btn btn-secondary">
        Manage Team
    </a>
{% endif %}
{% endblock %}

{% block tab_about %}
<div class="team-description">
    {{ team.description|linebreaks }}
</div>

<div class="team-requirements">
    <h3>Looking For</h3>
    {% if team.needed_roles %}
    <ul class="role-list">
        {% for role in team.needed_roles %}
        <li class="role-badge role-{{ role }}">{{ role|title }}</li>
        {% endfor %}
    </ul>
    {% else %}
    <p>Team is complete</p>
    {% endif %}
</div>
{% endblock %}

{% block tab_skills %}
<h3>Team Members</h3>
<div class="members-grid">
    {% for membership in team.membership.all %}
    <div class="member-card">
        <div class="member-avatar">
            {% if membership.user.avatar %}
                <img src="{{ membership.user.avatar.url }}" alt="{{ membership.user.get_full_name }}">
            {% else %}
                <span class="avatar-placeholder">{{ membership.user.get_initials }}</span>
            {% endif %}
        </div>
        <div class="member-info">
            <h4><a href="{% url 'users:profile' membership.user.username %}">{{ membership.user.get_full_name }}</a></h4>
            <span class="member-role role-{{ membership.role }}">
                {{ membership.get_role_display }}
            </span>
            {% if membership.is_leader %}
                <span class="leader-badge">Team Leader</span>
            {% endif %}
            <div class="member-joined">
                Joined: {{ membership.joined_at|date:"M d, Y" }}
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% endblock %}

{% block tab_projects %}
<h3>Submissions</h3>
{% if team.submissions.exists %}
    <div class="submissions-timeline">
        {% for submission in team.submissions.all %}
        <div class="submission-item status-{{ submission.verification_status }}">
            <div class="submission-header">
                <span class="submission-date">
                    {{ submission.submitted_at|date:"M d, Y H:i" }}
                </span>
                {% include "components/verification-badge.html" with status=submission.verification_status %}
            </div>
            {% if submission.score %}
            <div class="submission-score">
                Score: {{ submission.score }}
            </div>
            {% endif %}
            {% if submission.feedback %}
            <div class="submission-feedback">
                {{ submission.feedback|linebreaks }}
            </div>
            {% endif %}
        </div>
        {% endfor %}
    </div>
{% else %}
    <p class="no-submissions">No submissions yet</p>
{% endif %}
{% endblock %}

{% block badges %}
{# Team achievements/badges will go here in Phase 2 #}
<p class="coming-soon">Achievements coming soon!</p>
{% endblock %}
```

#### 4.3.5 User Profile Page
**Template**: `templates/pages/user_profile.html`

**Layout Structure**:
```markdown
[Profile Header - Full width]
- Avatar (large, 128px)
- Name, role preference (Hacker/Hipster/Hustler)
- XP: 2,450 | Level: 7 | Reputation: ★★★★☆
- Status: "Seeking team for next hackathon"
- Actions: [Message] [Invite to Team]

[Stats Bar]
- Hackathons: 12 | Teams: 5 | Quests: 89 | Win Rate: 33%

[Tab Content: Main (70%) + Sidebar (30%)]
Main: About | Skills | Projects | Teams | Activity
Sidebar: Badges, recent activity, team formation widget
```

#### 4.3.6 Dojo (Quest Listing)
**Template**: `templates/pages/quest_listing.html`

**Example Code**:
```django
{% extends "layouts/community_layout.html" %}

{% block filter_options %}
<div class="filter-group">
    <h4>Type</h4>
    <label><input type="checkbox" name="type" value="technical"> Technical</label>
    <label><input type="checkbox" name="type" value="commercial"> Commercial</label>
    <label><input type="checkbox" name="type" value="operational"> Operational</label>
</div>

<div class="filter-group">
    <h4>Difficulty</h4>
    <label><input type="radio" name="difficulty" value=""> All Levels</label>
    <label><input type="radio" name="difficulty" value="beginner"> Beginner</label>
    <label><input type="radio" name="difficulty" value="intermediate"> Intermediate</label>
    <label><input type="radio" name="difficulty" value="advanced"> Advanced</label>
    <label><input type="radio" name="difficulty" value="expert"> Expert</label>
</div>
{% endblock %}

{% block quick_stats %}
<div class="stat-item">
    <span class="stat-value">{{ total_quests }}</span>
    <span class="stat-label">Total Quests</span>
</div>
<div class="stat-item">
    <span class="stat-value">{{ user_completed }}</span>
    <span class="stat-label">You Completed</span>
</div>
{% endblock %}

{% block grid_items %}
{% for quest in quests %}
    {% include "components/quest-card.html" with quest=quest %}
{% empty %}
    <p class="no-quests">No quests match your filters</p>
{% endfor %}
{% endblock %}

{% block pagination %}
{% if quests.has_other_pages %}
    {% include "components/pagination.html" with page_obj=quests %}
{% endif %}
{% endblock %}
```

#### 4.3.7 Quest Detail Page
**Template**: `templates/pages/quest_detail.html`

**Layout Structure**:
```markdown
[Quest Header]
- Icon (large)
- Title
- Difficulty badge
- XP reward

[Two-column layout]
  [Left: Instructions - 60%]
  - Quest description (RichTextField)
  - Requirements checklist
  - Submission guidelines
  - Examples
  - Hints

  [Right: Submission Panel - 40%]
  - Status: Not Started | In Progress | Submitted | Verified
  - Submission form (if not completed):
    - Upload file OR paste URL
    - Description textarea
    - [Submit] button
  - OR Score & feedback (if verified)
  - Leaderboard (top 10 quest completions)
```

#### 4.3.8 Leaderboard Page
**Template**: `templates/pages/leaderboard.html`

**Layout Structure**:
```markdown
[Header]
- Title: "Leaderboard"
- Hackathon selector dropdown
- Filter: Teams | Individual

[Leaderboard Table - Full width]
Columns: Rank | Team/User | Score | Projects | Verifications | Trend
- Top 100 with pagination
- Highlight current user's team/rank
- Trend indicators: ↑ up, ↓ down, — same

[Optional Sidebar]
- Top Performers This Week
- Most Improved
- Upcoming Awards
```

### 4.4 Component Library Design

#### 4.4.1 Card Components

**Event Card** (`templates/components/event-card.html`):
```django
<div class="event-card">
    {% if event.cover_image %}
        {% image event.cover_image fill-400x225 as cover %}
        <img src="{{ cover.url }}" alt="{{ event.title }}" class="card-image">
    {% endif %}

    <div class="card-content">
        <h3 class="card-title">
            <a href="{{ event.url }}">{{ event.title }}</a>
        </h3>

        <div class="card-meta">
            <span class="status-badge status-{{ event.status }}">
                {{ event.get_status_display }}
            </span>

            {% if event.status == 'in_progress' or event.status == 'registration_open' %}
                {% include "components/countdown-timer.html" with end_date=event.get_current_phase.end_date only %}
            {% endif %}
        </div>

        <div class="card-stats">
            <div class="stat">
                <span class="stat-icon">👥</span>
                <span class="stat-value">{{ event.teams.count }}</span>
                <span class="stat-label">teams</span>
            </div>
            <div class="stat">
                <span class="stat-icon">📅</span>
                <span class="stat-value">{{ event.start_date|date:"M d" }}</span>
            </div>
        </div>

        <div class="card-actions">
            <a href="{{ event.url }}" class="btn btn-sm btn-primary">View Details</a>
        </div>
    </div>
</div>
```

**Team Card** (`templates/components/team-card.html`):
```django
<div class="team-card">
    <div class="team-card-header">
        <h3 class="team-name">
            <a href="{% url 'hackathons:team_profile' team.hackathon.slug team.slug %}">
                {{ team.name }}
            </a>
        </h3>
        {% if team.tagline %}
        <p class="team-tagline">{{ team.tagline }}</p>
        {% endif %}
    </div>

    <div class="team-card-body">
        <div class="team-members-preview">
            {% for membership in team.membership.all|slice:":5" %}
            <div class="member-avatar-sm" title="{{ membership.user.get_full_name }}">
                {{ membership.user.get_initials }}
            </div>
            {% endfor %}
            {% if team.members.count > 5 %}
            <div class="member-overflow">+{{ team.members.count|add:"-5" }}</div>
            {% endif %}
        </div>

        {% if team.needed_roles %}
        <div class="team-needs">
            <strong>Need:</strong>
            {% for role in team.needed_roles %}
            <span class="role-badge role-{{ role }}">{{ role|title }}</span>
            {% endfor %}
        </div>
        {% endif %}
    </div>

    <div class="team-card-footer">
        <span class="team-status status-{{ team.status }}">
            {{ team.get_status_display }}
        </span>

        {% if team.status == 'looking_for_members' and user.is_authenticated %}
        <button class="btn btn-sm btn-secondary" onclick="applyToTeam({{ team.id }})">
            Apply
        </button>
        {% else %}
        <a href="{% url 'hackathons:team_profile' team.hackathon.slug team.slug %}" class="btn btn-sm btn-outline">
            View Team
        </a>
        {% endif %}
    </div>
</div>
```

**Quest Card** (`templates/components/quest-card.html`):
```django
<div class="quest-card">
    <div class="quest-icon">
        {% if quest.icon %}
            {{ quest.icon }}
        {% else %}
            <span class="icon-placeholder">🎯</span>
        {% endif %}
    </div>

    <div class="quest-content">
        <h3 class="quest-title">
            <a href="{% url 'hackathons:quest_detail' quest.slug %}">{{ quest.title }}</a>
        </h3>

        <div class="quest-badges">
            <span class="badge badge-difficulty badge-{{ quest.difficulty }}">
                {{ quest.get_difficulty_display }}
            </span>
            <span class="badge badge-type badge-{{ quest.quest_type }}">
                {{ quest.get_quest_type_display }}
            </span>
        </div>

        <p class="quest-description">{{ quest.description|striptags|truncatewords:20 }}</p>

        <div class="quest-footer">
            <div class="quest-reward">
                <span class="icon">⭐</span>
                <span class="value">{{ quest.xp_reward }} XP</span>
            </div>
            <div class="quest-time">
                <span class="icon">⏱</span>
                <span class="value">{{ quest.estimated_time_minutes }} min</span>
            </div>
            <div class="quest-completion">
                <span class="icon">👥</span>
                <span class="value">{{ quest.completions_count }} completed</span>
            </div>
        </div>

        <div class="quest-actions">
            <a href="{% url 'hackathons:quest_detail' quest.slug %}" class="btn btn-primary btn-block">
                Start Quest
            </a>
        </div>
    </div>
</div>
```

**Participant Card** (`templates/components/participant-card.html`):
```django
<div class="participant-card">
    <div class="participant-avatar">
        {% if participant.avatar %}
            <img src="{{ participant.avatar.url }}" alt="{{ participant.get_full_name }}">
        {% else %}
            <span class="avatar-placeholder">{{ participant.get_initials }}</span>
        {% endif %}
    </div>

    <div class="participant-info">
        <h4 class="participant-name">
            <a href="{% url 'users:profile' participant.username %}">
                {{ participant.get_full_name }}
            </a>
        </h4>

        {% if participant.preferred_role %}
        <span class="role-badge role-{{ participant.preferred_role }}">
            {{ participant.get_preferred_role_display }}
        </span>
        {% endif %}

        {% if participant.skills %}
        <div class="participant-skills">
            {% for skill in participant.skills|slice:":3" %}
            <span class="skill-tag">{{ skill }}</span>
            {% endfor %}
            {% if participant.skills|length > 3 %}
            <span class="skill-more">+{{ participant.skills|length|add:"-3" }}</span>
            {% endif %}
        </div>
        {% endif %}

        <div class="participant-reputation">
            {% include "components/reputation-stars.html" with score=participant.reputation_score %}
        </div>

        <div class="participant-actions">
            <a href="{% url 'users:profile' participant.username %}" class="btn btn-sm btn-outline">
                View Profile
            </a>
            {% if user.is_authenticated and user.is_team_leader %}
            <button class="btn btn-sm btn-primary" onclick="inviteToTeam({{ participant.id }})">
                Invite
            </button>
            {% endif %}
        </div>
    </div>
</div>
```

**Project Card** (`templates/components/project-card.html`):
```django
<div class="project-card">
    {% if project.screenshot %}
        {% image project.screenshot fill-400x225 as screenshot %}
        <img src="{{ screenshot.url }}" alt="{{ project.title }}" class="card-image">
    {% endif %}

    <div class="card-content">
        <h3 class="project-title">{{ project.title }}</h3>

        <div class="project-team">
            <a href="{% url 'hackathons:team_profile' project.team.hackathon.slug project.team.slug %}">
                {{ project.team.name }}
            </a>
        </div>

        <div class="project-status">
            {% include "components/verification-badge.html" with status=project.verification_status %}

            {% if project.score %}
            <span class="project-score">
                Score: <strong>{{ project.score }}</strong>
            </span>
            {% endif %}
        </div>

        {% if project.description %}
        <p class="project-description">{{ project.description|truncatewords:30 }}</p>
        {% endif %}

        <div class="card-actions">
            {% if project.submission_url %}
            <a href="{{ project.submission_url }}" target="_blank" class="btn btn-sm btn-outline">
                View Project
            </a>
            {% endif %}
        </div>
    </div>
</div>
```

#### 4.4.2 Interactive Components

**Countdown Timer** (`templates/components/countdown-timer.html`):
```django
<div class="countdown-timer"
     x-data="countdown('{{ end_date|date:'c' }}')"
     x-init="start()">
    <div class="countdown-segment">
        <span class="countdown-value" x-text="days">0</span>
        <span class="countdown-label">days</span>
    </div>
    <div class="countdown-segment">
        <span class="countdown-value" x-text="hours">0</span>
        <span class="countdown-label">hours</span>
    </div>
    <div class="countdown-segment">
        <span class="countdown-value" x-text="minutes">0</span>
        <span class="countdown-label">min</span>
    </div>
    <div class="countdown-segment">
        <span class="countdown-value" x-text="seconds">0</span>
        <span class="countdown-label">sec</span>
    </div>
</div>

<script>
function countdown(endDateISO) {
    return {
        days: 0,
        hours: 0,
        minutes: 0,
        seconds: 0,
        interval: null,

        start() {
            this.update();
            this.interval = setInterval(() => this.update(), 1000);
        },

        update() {
            const end = new Date(endDateISO);
            const now = new Date();
            const diff = end - now;

            if (diff <= 0) {
                clearInterval(this.interval);
                this.days = this.hours = this.minutes = this.seconds = 0;
                return;
            }

            this.days = Math.floor(diff / (1000 * 60 * 60 * 24));
            this.hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            this.minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            this.seconds = Math.floor((diff % (1000 * 60)) / 1000);
        }
    };
}
</script>
```

**Phase Timeline** (`templates/components/phase-timeline.html`):
```django
<div class="phase-timeline">
    {% for phase in phases %}
    <div class="phase-item {% if phase.is_active %}active{% elif phase.is_completed %}completed{% endif %}">
        <div class="phase-marker">
            <span class="phase-number">{{ forloop.counter }}</span>
        </div>
        <div class="phase-connector"></div>
        <div class="phase-content">
            <h4 class="phase-title">{{ phase.title }}</h4>
            <p class="phase-dates">
                {{ phase.start_date|date:"M d" }} - {{ phase.end_date|date:"M d, Y" }}
            </p>
            {% if phase.description %}
            <p class="phase-description">{{ phase.description }}</p>
            {% endif %}
        </div>
    </div>
    {% endfor %}
</div>
```

**Team Formation Widget** (`templates/components/team-formation-widget.html`):
```django
<div class="team-formation-widget" x-data="{ role: '' }">
    <h4>Find Your Team</h4>

    <div class="role-selector">
        <label>I am a:</label>
        <div class="role-options">
            <button @click="role = 'hacker'"
                    :class="{ active: role === 'hacker' }"
                    class="role-option role-hacker">
                💻 Hacker
            </button>
            <button @click="role = 'hipster'"
                    :class="{ active: role === 'hipster' }"
                    class="role-option role-hipster">
                🎨 Hipster
            </button>
            <button @click="role = 'hustler'"
                    :class="{ active: role === 'hustler' }"
                    class="role-option role-hustler">
                📈 Hustler
            </button>
        </div>
    </div>

    <div class="widget-actions">
        <a href="{% url 'hackathons:teams' %}?role=" :href="'{% url 'hackathons:teams' %}?role=' + role"
           class="btn btn-primary btn-block"
           :disabled="!role">
            Find Teams
        </a>
    </div>
</div>
```

**Stats Panel** (`templates/components/stats-panel.html`):
```django
<div class="stats-panel">
    <div class="stat-item">
        <span class="stat-icon">👥</span>
        <div class="stat-content">
            <span class="stat-value">{{ stats.teams_count }}</span>
            <span class="stat-label">Teams</span>
        </div>
    </div>

    <div class="stat-item">
        <span class="stat-icon">👤</span>
        <div class="stat-content">
            <span class="stat-value">{{ stats.participants_count }}</span>
            <span class="stat-label">Participants</span>
        </div>
    </div>

    <div class="stat-item">
        <span class="stat-icon">📦</span>
        <div class="stat-content">
            <span class="stat-value">{{ stats.submissions_count }}</span>
            <span class="stat-label">Submissions</span>
        </div>
    </div>
</div>
```

**Verification Badge** (`templates/components/verification-badge.html`):
```django
<span class="verification-badge status-{{ status }}"
      title="{{ status|capfirst }}">
    {% if status == 'pending' %}
        <span class="badge-icon">⏱</span>
        <span class="badge-text">Pending Review</span>
    {% elif status == 'verified' %}
        <span class="badge-icon">✓</span>
        <span class="badge-text">Verified</span>
    {% elif status == 'rejected' %}
        <span class="badge-icon">✗</span>
        <span class="badge-text">Rejected</span>
    {% endif %}
</span>
```

**Leaderboard** (`templates/components/leaderboard.html`):
```django
<div class="leaderboard">
    <table class="leaderboard-table">
        <thead>
            <tr>
                <th>Rank</th>
                <th>Team</th>
                <th>Members</th>
                <th>Score</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {% for team in teams %}
            <tr class="{% if user.is_authenticated and user in team.members.all %}highlight{% endif %}">
                <td class="rank-cell">
                    {% if forloop.counter <= 3 %}
                        <span class="rank-medal rank-{{ forloop.counter }}">
                            {% if forloop.counter == 1 %}🥇
                            {% elif forloop.counter == 2 %}🥈
                            {% else %}🥉{% endif %}
                        </span>
                    {% else %}
                        <span class="rank-number">{{ forloop.counter }}</span>
                    {% endif %}
                </td>
                <td class="team-cell">
                    <a href="{% url 'hackathons:team_profile' team.hackathon.slug team.slug %}">
                        {{ team.name }}
                    </a>
                </td>
                <td class="members-cell">{{ team.members.count }}</td>
                <td class="score-cell"><strong>{{ team.final_score|default:"—" }}</strong></td>
                <td class="status-cell">
                    <span class="status-badge status-{{ team.status }}">
                        {{ team.get_status_display }}
                    </span>
                </td>
            </tr>
            {% empty %}
            <tr>
                <td colspan="5" class="no-teams">No teams yet</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
```

### 4.5 Navigation Updates

#### 4.5.1 Header Navigation
**File**: `templates/navigation/header.html`

**Changes needed**:
```django
{# Update main navigation links #}
<nav class="main-nav">
    <ul>
        <li><a href="/">Home</a></li>
        <li><a href="{% url 'hackathons:list' %}">Hackathons</a></li>  {# Changed from "Events" #}
        <li><a href="{% url 'hackathons:dojo' %}">Dojo</a></li>  {# NEW: Quest listing #}
        <li><a href="{% url 'hackathons:teams' %}">Teams</a></li>  {# NEW: Team browsing #}
        <li><a href="{% url 'pages:announcements' %}">News</a></li>  {# Changed from generic news #}

        {% if user.is_authenticated %}
            <li class="user-menu" x-data="{ open: false }">
                <button @click="open = !open" class="user-menu-toggle">
                    <div class="user-avatar-sm">{{ user.get_initials }}</div>
                    <span class="user-name">{{ user.get_full_name }}</span>
                    <span class="user-xp">⭐ {{ user.xp_points }} XP</span>
                </button>

                <div x-show="open" @click.away="open = false" class="user-dropdown">
                    <a href="{% url 'users:profile' user.username %}">My Profile</a>
                    <a href="{% url 'users:dashboard' %}">Dashboard</a>
                    <a href="{% url 'users:settings' %}">Settings</a>
                    <hr>
                    <a href="{% url 'logout' %}">Logout</a>
                </div>
            </li>
        {% else %}
            <li><a href="{% url 'login' %}" class="btn btn-sm btn-outline">Login</a></li>
            <li><a href="{% url 'signup' %}" class="btn btn-sm btn-primary">Sign Up</a></li>
        {% endif %}
    </ul>
</nav>
```

#### 4.5.2 Footer Navigation
**File**: `templates/navigation/footer.html`

**Changes needed**:
```django
<footer class="site-footer">
    <div class="container">
        <div class="footer-columns">
            <div class="footer-column">
                <h4>Platform</h4>
                <ul>
                    <li><a href="{% url 'hackathons:list' %}">Browse Hackathons</a></li>
                    <li><a href="{% url 'hackathons:dojo' %}">Dojo Challenges</a></li>
                    <li><a href="{% url 'hackathons:teams' %}">Find a Team</a></li>
                    <li><a href="{% url 'hackathons:leaderboard' %}">Leaderboard</a></li>
                </ul>
            </div>

            <div class="footer-column">
                <h4>For Organizers</h4>
                <ul>
                    <li><a href="{% url 'pages:organizer-guide' %}">Organizer Guide</a></li>
                    <li><a href="{% url 'pages:developer-guide' %}">Developer Guide</a></li>
                    <li><a href="/admin/">Admin Portal</a></li>
                </ul>
            </div>

            <div class="footer-column">
                <h4>Resources</h4>
                <ul>
                    <li><a href="{% url 'pages:api-docs' %}">API Documentation</a></li>
                    <li><a href="{% url 'pages:faq' %}">FAQ</a></li>
                    <li><a href="https://github.com/synnovator" target="_blank">GitHub</a></li>
                </ul>
            </div>

            <div class="footer-column">
                <h4>Company</h4>
                <ul>
                    <li><a href="{% url 'pages:about' %}">About</a></li>
                    <li><a href="{% url 'pages:contact' %}">Contact</a></li>
                    <li><a href="{% url 'pages:terms' %}">Terms</a></li>
                    <li><a href="{% url 'pages:privacy' %}">Privacy</a></li>
                </ul>
            </div>
        </div>

        {# Keep existing social links and newsletter #}
        {{ block.super }}
    </div>
</footer>
```

### 4.6 Design System Updates

#### 4.6.1 Color Palette Additions

Add to `tailwind.config.js`:
```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        // Keep existing mackerel palette
        mackerel: {
          100: '#E0F2F5',
          200: '#96D7E5',
          300: '#26899E',
          400: '#1A2A2E',
          // ...
        },

        // Add status colors
        success: {
          50: '#ECFDF5',
          100: '#D1FAE5',
          500: '#10B981',  // Primary success
          600: '#059669',
        },
        warning: {
          50: '#FFFBEB',
          100: '#FEF3C7',
          500: '#F59E0B',  // Primary warning
          600: '#D97706',
        },
        error: {
          50: '#FEF2F2',
          100: '#FEE2E2',
          500: '#EF4444',  // Primary error
          600: '#DC2626',
        },
        info: {
          50: '#EFF6FF',
          100: '#DBEAFE',
          500: '#3B82F6',  // Primary info
          600: '#2563EB',
        },
      },

      // Add animation for countdown timer
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
}
```

#### 4.6.2 Typography Usage

**Font Usage Guide**:
- **Serif (Source Serif 4)**: Page titles, hero text, hackathon names, event titles
- **Sans (Source Sans 3)**: Body text, descriptions, UI text, buttons
- **Mono (Source Code Pro)**: Metadata, stats, countdown timers, code snippets

#### 4.6.3 Spacing & Layout Tokens

**Standard Spacing**:
- Card padding: `p-6` (24px)
- Section spacing: `gap-8` (32px) or `lg:gap-10` (40px)
- Grid gaps: `gap-4` (16px) for dense layouts, `gap-6` (24px) for spacious
- Container max-width: `1512px` (`.site-container`)

**Card Styling Patterns**:
```css
/* Default card */
.card {
  @apply shadow-md hover:shadow-lg transition-shadow duration-200;
  @apply border border-grey-200 dark:border-grey-700 rounded-lg;
  @apply p-6;
}

/* Interactive card */
.card-interactive {
  @apply cursor-pointer hover:scale-105 transform transition-transform;
}
```

### 4.7 Responsive Design Strategy

#### 4.7.1 Breakpoint Usage
- **Mobile** (< 768px): Single-column layouts, stacked cards
- **Tablet** (768px - 1024px): 2-column grids, horizontal cards
- **Desktop** (≥ 1024px): 3-column grids, fixed sidebars, multi-column layouts

#### 4.7.2 Layout Adaptations

**Mobile (< 768px)**:
- Single-column layouts
- Stacked cards (no grid)
- Bottom navigation bar (optional)
- Full-screen modals
- Hamburger menu

**Tablet (768px - 1024px)**:
- 2-column grids
- Horizontal cards (image left, content right)
- Slide-out sidebar for filters

**Desktop (≥ 1024px)**:
- 3-column grids
- Fixed sidebars (dashboard, filters)
- Multi-column layouts (main + sidebar)
- Modal dialogs (not full-screen)

### 4.8 Animation & Interaction Patterns

#### 4.8.1 Micro-interactions
```css
/* Button hover */
.btn {
  @apply hover:scale-105 hover:shadow-lg transition-all duration-200;
}

/* Card hover */
.card {
  @apply hover:shadow-xl transition-shadow duration-300;
}

/* Status badges */
.status-badge.status-pending {
  @apply animate-pulse;
}
```

#### 4.8.2 Alpine.js Interactions
- **Tab switching**: `x-transition` (fade)
- **Countdown timer**: Live updates every second
- **Dropdowns**: `x-show` with `@click.away`
- **Modals**: `x-transition` with overlay

### 4.9 Templates to Keep (Base Components)

**No changes needed:**
- `templates/base.html` - Base layout (will add layout switching logic)
- `templates/components/button.html` - Generic button component
- `templates/components/pagination.html` - Pagination
- `templates/components/icon.html` - SVG icons
- `templates/components/form-field.html` - Form inputs

### 4.10 Templates to Archive

**Move to `templates/_archived/`:**
- `templates/pages/article_page.html` → Replaced by announcement templates
- `templates/pages/news_listing_page.html` → Replaced by announcement listing
- `templates/components/card--article.html` → Use generic card with different data

### 4.11 Templates to Remove

**Delete these hackathon-superseded templates:**
- `templates/pages/event_page.html` → Replaced by `hackathon_page.html`
- `templates/pages/event_listing_page.html` → Replaced by `hackathon_listing_page.html`
- `templates/pages/event_participants_page.html` → Replaced by `team_profile.html`

### 4.12 Implementation File Structure

```
templates/
├── base.html                           # Keep existing, add layout switching
├── layouts/                            # NEW
│   ├── dashboard_layout.html          # Sidebar + main content
│   ├── community_layout.html          # Filter sidebar + grid
│   ├── event_layout.html              # Event header + tabs
│   └── profile_layout.html            # Profile header + tabs
├── pages/
│   ├── home_page.html                 # UPDATE: Community dashboard
│   ├── hackathon_listing_page.html    # NEW: Filtered event grid
│   ├── hackathon_page.html            # NEW: Event dashboard
│   ├── team_profile.html              # NEW: Team showcase
│   ├── user_profile.html              # NEW: User profile
│   ├── quest_listing.html             # NEW: Dojo challenges
│   ├── quest_detail.html              # NEW: Challenge view
│   └── leaderboard.html               # NEW: Rankings
├── components/
│   ├── event-card.html                # NEW
│   ├── team-card.html                 # NEW
│   ├── participant-card.html          # NEW
│   ├── project-card.html              # NEW
│   ├── quest-card.html                # NEW
│   ├── countdown-timer.html           # NEW
│   ├── phase-timeline.html            # NEW
│   ├── team-formation-widget.html     # NEW
│   ├── stats-panel.html               # NEW
│   ├── verification-badge.html        # NEW
│   ├── leaderboard.html               # NEW
│   ├── prize-card.html                # NEW
│   ├── breadcrumbs.html               # NEW
│   ├── reputation-stars.html          # NEW
│   ├── card.html                      # KEEP
│   ├── button.html                    # KEEP
│   ├── pagination.html                # KEEP
│   └── form-field.html                # KEEP
├── navigation/
│   ├── header.html                    # UPDATE: Add user dropdown, XP
│   └── footer.html                    # UPDATE: Update links
└── _archived/                          # NEW: Move old templates here
    ├── article_page.html
    ├── news_listing_page.html
    └── event_page.html
```

### 4.13 Migration Strategy

#### Phase 1: Layout Templates (Week 3-4)
1. Create 4 base layout templates (dashboard, community, event, profile)
2. Update `base.html` to support multiple layout types
3. Test layout switching logic

#### Phase 2: Component Library (Week 4-5)
1. Create all card components (event, team, participant, project, quest)
2. Create interactive components (countdown, team formation, stats)
3. Update navigation components (header, footer)

#### Phase 3: Page Templates (Week 5-7)
1. Update home page to community dashboard
2. Create hackathon listing and detail pages
3. Create team and user profile pages
4. Create dojo (quest) pages
5. Create leaderboard page

#### Phase 4: Styling & Polish (Week 7-8)
1. Add status colors and design tokens
2. Implement Alpine.js interactions
3. Test responsive layouts
4. Archive old templates

### 4.14 Success Criteria

Layout refactoring is complete when:
- [ ] All 4 base layouts created and functional
- [ ] 15+ new components implemented
- [ ] All 8 key pages use new layouts
- [ ] Navigation updated with hackathon terminology
- [ ] Mobile, tablet, desktop layouts tested
- [ ] Dark mode works on all new components
- [ ] Alpine.js interactions smooth and performant
- [ ] Old templates archived in `templates/_archived/`
- [ ] No references to "blog", "article", "news" in hackathon UI
- [ ] User acceptance: Platform feels like a community, not a news site

---
