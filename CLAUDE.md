# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Synnovator is an AI-powered hackathon platform built on Wagtail CMS and Django. The platform implements an "Events as Code" architecture to manage hackathons, with strong social features for team formation and automated verification systems. It serves OPC (Operations, Product/Commercial, Technology) teams in creating and managing AI-focused innovation challenges.

Key philosophy: The platform does NOT host user code - it orchestrates connections between participants, Git repositories, and automated verification services (via webhooks to CI/CD systems like GitHub Actions).

## Commands

### Development with uv (Python Package Manager)

**IMPORTANT**: This project uses `uv` for Python package management. All Python commands should be executed with `uv`:

```bash
# Install dependencies
uv sync

# Run Django commands
uv run python manage.py <command>
```

### Common Development Commands

```bash
# Start development server
make start
# or: uv run python manage.py runserver

# Initialize database with demo data
make init
# or run steps manually:
# uv run python manage.py createcachetable
# uv run python manage.py migrate
# uv run python manage.py load_initial_data
# uv run python manage.py collectstatic --noinput

# Reset database (dangerous - deletes all data)
make reset-db

# Dump current data to fixtures
make dump-data

# Database migrations
uv run python manage.py makemigrations
uv run python manage.py migrate

# Create superuser
uv run python manage.py createsuperuser
# Default credentials: admin/password
```

### Frontend Build Commands

```bash
# Development build with watch mode
npm run start

# Production build
npm run build:prod

# Development build (one-time)
npm run build

# Development server with hot reload
npm run start:reload
```

### Testing

```bash
# Run tests
uv run python manage.py test

# Run specific test
uv run python manage.py test synnovator.home.tests.TestHomePage
```

### Browser Automation

Use `agent-browser` for web automation. Run `agent-browser --help` for all commands.

Core workflow:
1. `agent-browser open <url>` - Navigate to page
2. `agent-browser snapshot -i` - Get interactive elements with refs (@e1, @e2)
3. `agent-browser click @e1` / `fill @e2 "text"` - Interact using refs
4. Re-snapshot after page changes

## Architecture

### Django/Wagtail Structure

- **synnovator/** - Main Django project package
  - **settings/** - Environment-specific settings (base.py, dev.py, production.py)
  - **home/** - Homepage models and views
  - **news/** - News/blog functionality
  - **users/** - Custom user model (AUTH_USER_MODEL = "users.User")
  - **images/** - Custom image model (WAGTAILIMAGES_IMAGE_MODEL = "images.CustomImage")
  - **forms/** - Form pages and blocks
  - **navigation/** - Navigation components
  - **search/** - Search functionality
  - **standardpages/** - Standard page types
  - **utils/** - Shared utilities and blocks

### Frontend Architecture

- **static_src/** - Source files for frontend assets
- **static_compiled/** - Webpack build output (committed to repo)
- **static/** - Collected static files (Django collectstatic output)
- **templates/** - Django/Wagtail templates
  - Uses template inheritance from base.html
  - Component-based structure in templates/components/

Frontend uses Webpack + Tailwind CSS + PostCSS for asset pipeline.

### Database

- Development: SQLite (db.sqlite3)
- Production: PostgreSQL via DATABASE_URL environment variable
- Uses dj-database-url for database configuration

### Storage

- Local: FileSystemStorage for media
- Cloud: Configurable S3-compatible storage (django-storages + wagtail-storages)
  - Set AWS_STORAGE_BUCKET_NAME to enable
  - Supports custom domains via AWS_S3_CUSTOM_DOMAIN

## Events as Code Philosophy

The core innovation of Synnovator is treating event configuration as code:

1. **Event Configuration**: Stored in Git repositories as YAML manifests (hackathon.yaml)
2. **Version Control**: All rule changes tracked via Git commits
3. **Git-Based CMS**: Non-technical users edit via UI, which generates Git commits
4. **Webhook Integration**: External CI/CD systems (GitHub Actions) send verification results back via webhooks
5. **Zero Code Hosting**: Platform stores metadata (repo URLs, commit hashes) but never the actual participant code

When implementing features:
- Event rules should be declarative and stored in Git
- Verification logic runs externally (not on Synnovator servers)
- All participant submissions link to Git repositories
- Use webhooks for asynchronous communication with external services

## Key Technical Patterns

### Custom User Model
The project uses a custom user model. Always reference users via:
```python
from django.conf import settings
User = settings.AUTH_USER_MODEL  # or "users.User"
```

### Wagtail Pages vs Django Views
- Content pages: Use Wagtail page models (inherit from Page)
- Dynamic features: May need traditional Django views alongside Wagtail pages
- Wagtail admin: Accessible at /admin/ (not /admin/ like Django)

### Environment Variables
Key environment variables:
- `SECRET_KEY` - Django secret (required in production)
- `DATABASE_URL` - PostgreSQL connection string
- `ALLOWED_HOSTS` - Comma-separated list
- `CSRF_TRUSTED_ORIGINS` - Comma-separated list for CSRF
- `AWS_STORAGE_BUCKET_NAME` - Enables S3 storage
- `CACHE_CONTROL_S_MAXAGE` - CDN cache duration (default: 600)

### Static Files
- Source files go in static_src/
- Run `npm run build:prod` before deploying
- Run `python manage.py collectstatic` to gather files into static/
- Production uses ManifestStaticFilesStorage for cache-busting

## Security Considerations

1. **Webhook Signature Verification**: All incoming webhooks from CI/CD must verify HMAC SHA-256 signatures
2. **No Code Execution**: Never execute user-submitted code on Synnovator servers
3. **Secrets Management**: Use encrypted fields for storing API keys/credentials that need to be distributed to participants
4. **Git Repository Access**: Only store public repository URLs or properly scoped OAuth tokens

## Database Schema Patterns

Key models to understand:
- `User` (users.User) - Custom user with role field (commercial/operational/technical)
- `CustomImage` (images.CustomImage) - Custom image model for Wagtail
- Future: Verification logs should store complete webhook payloads as JSONB for audit trails
- Future: Consider GraphDB (Neo4j) for user skill graphs and team relationship modeling

## Product Context

Reference spec/hackathon-prd.md for detailed product requirements. Key user personas:
- **Organizer (COO)** - Configures events, manages operations
- **Organizer (CBO)** - Identifies business potential, curates projects
- **Organizer (CTO)** - Sets technical standards, manages verification workflows
- **Participant** - Competes in hackathons, seeks team members, builds reputation

Core features to implement:
1. Events as Code engine (Git-backed configuration)
2. Team formation with role-based matching (Hacker/Hipster/Hustler)
3. Automated verification via CI/CD webhooks
4. High-frequency "Dojo" challenges for continuous engagement
5. Skill verification based on Git history analysis

## Local File Paths

When testing or referencing files locally, note that:
- Project root: /Users/allenwoods/Sync/2-engineering/ssd
- Python version: 3.12 (see .python-version)
- Virtual environment: .venv/ (managed by uv)
