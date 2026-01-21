## Section 11: Technology Additions

### 11.1 Python Dependencies (MVP - Phase 1)

**Good news: NO new backend dependencies required for MVP!**

The MVP uses standard Django/Wagtail functionality already present in the project. No PyYAML, no requests, no GitPython, no cryptography needed.

**Optional for MVP:**
```toml
[project]
dependencies = [
    # All existing Wagtail/Django dependencies remain unchanged

    # Optional: For security (XSS prevention in user-generated content)
    "bleach>=6.1.0",  # Only if rendering markdown/rich text

    # Optional: For rate limiting
    "django-ratelimit>=4.1.0",  # Prevent submission abuse

    # Optional: For virus scanning (production only)
    # Install ClamAV separately via system package manager
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.3",
    "pytest-django>=4.7.0",
    "pytest-cov>=4.1.0",
    "factory-boy>=3.3.0",  # Test fixtures
]
```

**Dependencies Deferred to Phase 3:**
- ❌ `PyYAML>=6.0.1` - Git YAML parsing (Phase 3)
- ❌ `requests>=2.31.0` - Git API calls (Phase 3)
- ❌ `gitpython>=3.1.40` - Git operations (Phase 3)
- ❌ `cryptography>=42.0.0` - Webhook secret encryption (Phase 3)
- ❌ `celery>=5.3.4` - Async tasks (Phase 3)
- ❌ `redis>=5.0.1` - Caching (Phase 3)
- ❌ `djangorestframework>=3.14.0` - REST API (Phase 3)

See `spec/future/git-integrate.md` for Phase 3 dependency list.

### 11.2 Frontend Dependencies

**Add to `package.json` (if not already present):**

```json
{
  "dependencies": {
    "alpinejs": "^3.13.3",
    "chart.js": "^4.4.1",
    "@tailwindcss/forms": "^0.5.7"
  },
  "devDependencies": {
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.4.0",
    "webpack": "^5.89.0",
    "webpack-cli": "^5.1.4"
  }
}
```

**Usage:**
- **Alpine.js** - Interactive team formation widgets, quest filters
- **Chart.js** - Leaderboard visualizations, user XP progress
- **Tailwind CSS** - Already in project, continue using for styling

### 11.3 Services & Infrastructure

#### 11.3.1 Development (MVP)
- **Database:** SQLite (existing) - Works fine for < 100 participants
- **Cache:** In-memory Django cache (existing)
- **Storage:** Local filesystem (existing)
- **No external services required!**

#### 11.3.2 Production (MVP)
- **Database:** PostgreSQL (existing via DATABASE_URL)
- **Storage:** S3-compatible (existing Wagtail setup via django-storages)
- **Cache:** In-memory or simple Redis (optional)
- **Monitoring:** Sentry (optional, if already configured)

**No new infrastructure for MVP!**

#### 11.3.3 Phase 3 Additions
When scaling beyond MVP:
- **Redis** - Leaderboard caching, session storage
- **Celery** - Async Git sync, background tasks
- **Message Queue** - Redis or RabbitMQ for Celery
- **CDN** - CloudFront or Cloudflare for static assets

### 11.4 Development Tools

**Recommended but not required:**

```toml
[project.optional-dependencies]
dev = [
    # Testing
    "pytest>=7.4.3",
    "pytest-django>=4.7.0",
    "pytest-cov>=4.1.0",
    "factory-boy>=3.3.0",

    # Code quality
    "ruff>=0.1.9",  # Linter and formatter
    "mypy>=1.8.0",  # Type checking
    "django-stubs>=4.2.7",  # Django type hints

    # Debugging
    "django-debug-toolbar>=4.2.0",
    "django-extensions>=3.2.3",  # shell_plus, graph_models

    # Documentation
    "mkdocs>=1.5.3",
    "mkdocs-material>=9.5.3",
]
```

### 11.5 Browser Requirements

**Supported browsers:**
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile: iOS Safari 14+, Chrome Android 90+

**Features used:**
- ES6 JavaScript (Alpine.js requirement)
- CSS Grid and Flexbox
- FormData API for file uploads
- Fetch API for AJAX

### 11.6 System Requirements

#### Development Environment
- Python 3.12+ (see `.python-version`)
- Node.js 18+ (for frontend build)
- uv (Python package manager, see CLAUDE.md)
- Git 2.30+
- 4GB RAM minimum
- 2GB free disk space

#### Production Environment
- Python 3.12+
- PostgreSQL 14+
- 2GB RAM minimum (for < 100 concurrent users)
- 10GB disk space (adjust based on submission volume)
- HTTPS certificate (Let's Encrypt recommended)

### 11.7 Optional Enhancements

**Can be added to MVP if desired:**

1. **Email Notifications:**
   ```toml
   # Already in Django, just configure SMTP:
   # settings/production.py
   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
   EMAIL_HOST = 'smtp.sendgrid.net'
   EMAIL_PORT = 587
   EMAIL_USE_TLS = True
   ```

2. **Social Auth (Phase 2):**
   ```toml
   "social-auth-app-django>=5.4.0",  # GitHub/GitLab OAuth
   ```

3. **Image Optimization:**
   ```toml
   "pillow-heif>=0.14.0",  # HEIF/HEIC support
   "django-imagekit>=5.0.0",  # Thumbnail generation
   ```

4. **Advanced Search (Phase 2):**
   ```toml
   "django-haystack>=3.2.1",
   "whoosh>=2.7.4",  # Or Elasticsearch
   ```

### 11.8 Technology Comparison

**MVP Approach vs. Original Plan:**

| Component | Original (Phase 1) | MVP (Simplified) | Saved |
|-----------|-------------------|------------------|-------|
| Backend Dependencies | 11 new packages | 0-2 new packages | ~9 packages |
| External Services | Git API, Redis, Celery | None | 100% |
| Configuration | YAML + DB | DB only | Simpler |
| Verification | Webhooks + HMAC | Manual in admin | Simpler |
| Complexity | High | Low | -60% |
| Time to Deploy | 8 weeks | 4-6 weeks | 2-4 weeks |

**When to Add Complexity:**
See `spec/future/git-integrate.md` for Phase 3 technology additions when platform reaches scale.

### 11.9 Future: Phase 3 Technology Stack

**Deferred to Phase 3 (when platform has 100+ participants):**

```toml
[project]
dependencies = [
    # Git integration
    "PyYAML>=6.0.1",
    "requests>=2.31.0",
    "gitpython>=3.1.40",

    # Webhook security
    "cryptography>=42.0.0",

    # Async processing
    "celery>=5.3.4",
    "redis>=5.0.1",

    # REST API
    "djangorestframework>=3.14.0",
    "djangorestframework-simplejwt>=5.3.1",
    "drf-spectacular>=0.27.0",

    # Monitoring
    "sentry-sdk>=1.40.0",
]
```

**Infrastructure for Phase 3:**
- Redis (caching + Celery broker)
- Message queue (RabbitMQ or Redis)
- CDN for static assets
- Webhook endpoint monitoring
- Git API rate limit monitoring

See `spec/future/git-integrate.md` for complete Phase 3 technology guide.

---
