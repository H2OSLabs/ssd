# Git Integration for Synnovator Hackathon Platform

**Status:** Future Enhancement (Phase 3)
**Prerequisites:** MVP must be stable with manual verification working
**Target:** Scale to 1000+ participants with automated verification
**Version:** 1.0
**Last Updated:** 2026-01-20

---

## Table of Contents

1. [Overview](#1-overview)
2. [When to Implement](#2-when-to-implement)
3. [Data Model Changes](#3-data-model-changes)
4. [Wagtail-to-Git Export](#4-wagtail-to-git-export)
5. [Git-to-Wagtail Import](#5-git-to-wagtail-import)
6. [Webhook Verification System](#6-webhook-verification-system)
7. [Security Implementation](#7-security-implementation)
8. [Migration Strategy](#8-migration-strategy)
9. [Dependencies](#9-dependencies)
10. [Implementation Checklist](#10-implementation-checklist)
11. [Testing Guide](#11-testing-guide)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Overview

### 1.1 Purpose

This document provides the complete implementation guide for adding Git integration and automated webhook verification to the Synnovator hackathon platform. These features were intentionally deferred from the MVP to reduce complexity and enable faster delivery.

### 1.2 Benefits

**Version Control:**
- All configuration changes tracked in Git history
- Know who changed what and when
- Easy revert to previous configurations
- Collaboration via pull requests

**Automation:**
- External CI/CD runs verification automatically
- Webhook endpoints receive results in real-time
- No manual score entry for objective tests
- Scales to 1000+ participants

**Transparency:**
- Public audit trail via Git commits
- Participants can see rule changes
- Configuration as code enables reproducibility

### 1.3 Architecture

**Bidirectional Sync:**
```
┌─────────────────┐         ┌──────────────────┐
│  Wagtail CMS    │◄───────►│  Git Repository  │
│  (PostgreSQL)   │  Export │  (hackathon.yaml)│
│                 │  Import │                  │
└────────┬────────┘         └──────────────────┘
         │
         │ Webhooks
         ▼
┌─────────────────┐         ┌──────────────────┐
│ Webhook Endpoint│◄────────│  GitHub Actions  │
│ (HMAC Verified) │  POST   │  GitLab CI       │
└─────────────────┘         └──────────────────┘
```

**Key Principle:** Git is the source of truth for hackathon configuration. Wagtail syncs FROM Git, not TO Git (to prevent accidental overwrites).

---

## 2. When to Implement

### 2.1 Trigger Criteria

Implement Git integration when ANY of these conditions are met:

✅ **Scale:**
- Platform consistently has > 100 submissions per hackathon
- Multiple concurrent hackathons running
- Daily quest submissions exceed 50

✅ **Operational Bottleneck:**
- Manual verification takes > 4 hours daily
- COO requests automated scoring
- Need 24/7 verification (no manual review delays)

✅ **Business Requirements:**
- Need public audit trail for compliance
- Require objective, repeatable scoring
- Want to support real-time verification during sprints

### 2.2 Prerequisites

Before implementing Git integration, ensure:

- [ ] MVP operational for at least 4-8 weeks
- [ ] Manual verification workflow fully tested
- [ ] Team familiar with Wagtail admin and scoring system
- [ ] At least 20 successful hackathon submissions manually verified
- [ ] Infrastructure supports Redis (for async tasks)
- [ ] Team has Git/webhook expertise

### 2.3 Risk Assessment

**Don't implement Git integration if:**
- MVP hasn't been battle-tested yet
- Platform has < 50 participants per event
- Manual verification is working well
- Team lacks DevOps/webhook experience
- Budget/timeline is tight

**Recommendation:** Wait until Phase 3 (Week 13-20) and MVP has proven value.

---

## 3. Data Model Changes

### 3.1 HackathonPage Model Updates

Add these fields to support Git integration:

**File:** `synnovator/hackathons/models/hackathon.py`

```python
from django.db import models
from wagtail.models import Page
from wagtail.admin.panels import FieldPanel, MultiFieldPanel

class HackathonPage(Page):
    # ... existing MVP fields ...

    # Git Integration Fields (Phase 3)
    git_repo_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="GitHub/GitLab repository URL (e.g., https://github.com/org/repo)"
    )

    git_branch = models.CharField(
        max_length=100,
        default='main',
        blank=True,
        help_text="Branch to sync from (main, master, develop)"
    )

    git_config_path = models.CharField(
        max_length=255,
        default='hackathon.yaml',
        blank=True,
        help_text="Path to hackathon.yaml in repository"
    )

    last_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last successful sync from Git"
    )

    last_sync_commit = models.CharField(
        max_length=40,
        blank=True,
        help_text="SHA of last synced commit"
    )

    sync_status = models.CharField(
        max_length=20,
        choices=[
            ('never', 'Never Synced'),
            ('success', 'Sync Successful'),
            ('failed', 'Sync Failed'),
            ('in_progress', 'Sync In Progress'),
        ],
        default='never'
    )

    sync_error_message = models.TextField(
        blank=True,
        help_text="Error details from last failed sync"
    )

    # Webhook Configuration
    webhook_secret = models.CharField(
        max_length=255,
        blank=True,
        help_text="HMAC secret for webhook signature verification (auto-generated)"
    )

    verification_provider = models.CharField(
        max_length=50,
        choices=[
            ('github_actions', 'GitHub Actions'),
            ('gitlab_ci', 'GitLab CI'),
            ('jenkins', 'Jenkins'),
            ('custom', 'Custom'),
        ],
        blank=True,
        help_text="External CI/CD system for automated verification"
    )

    # Admin panels
    git_panels = [
        MultiFieldPanel([
            FieldPanel('git_repo_url'),
            FieldPanel('git_branch'),
            FieldPanel('git_config_path'),
        ], heading="Git Repository Configuration"),
        MultiFieldPanel([
            FieldPanel('last_sync_at', read_only=True),
            FieldPanel('last_sync_commit', read_only=True),
            FieldPanel('sync_status', read_only=True),
            FieldPanel('sync_error_message', read_only=True),
        ], heading="Sync Status"),
        MultiFieldPanel([
            FieldPanel('verification_provider'),
            FieldPanel('webhook_secret', read_only=True),
        ], heading="Webhook Configuration"),
    ]

    # Add to existing content_panels
    content_panels = Page.content_panels + [
        # ... existing MVP panels ...
    ] + git_panels

    def save(self, *args, **kwargs):
        # Auto-generate webhook secret if not set
        if not self.webhook_secret and self.verification_provider:
            import secrets
            self.webhook_secret = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
```

### 3.2 VerificationLog Model (New)

Create audit trail for all webhook submissions:

**File:** `synnovator/hackathons/models/verification_log.py`

```python
from django.db import models
from django.contrib.postgres.fields import JSONField

class VerificationLog(models.Model):
    """
    Audit trail for automated webhook verifications.
    Stores complete webhook payload for debugging and compliance.
    """

    submission = models.ForeignKey(
        'Submission',
        on_delete=models.CASCADE,
        related_name='verification_logs'
    )

    hackathon = models.ForeignKey(
        'HackathonPage',
        on_delete=models.CASCADE,
        related_name='verification_logs'
    )

    # Webhook metadata
    provider = models.CharField(
        max_length=50,
        choices=[
            ('github_actions', 'GitHub Actions'),
            ('gitlab_ci', 'GitLab CI'),
            ('jenkins', 'Jenkins'),
            ('custom', 'Custom'),
        ]
    )

    webhook_payload = models.JSONField(
        help_text="Complete webhook payload (for audit and debugging)"
    )

    signature_verified = models.BooleanField(
        default=False,
        help_text="Whether HMAC signature was valid"
    )

    # Verification results
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('success', 'Success'),
            ('failed', 'Failed'),
            ('error', 'Error'),
        ]
    )

    score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Score calculated by external verification system"
    )

    test_results = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detailed test results (passed, failed, skipped)"
    )

    logs = models.TextField(
        blank=True,
        help_text="Build/test logs from external system"
    )

    # Timing
    received_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When webhook was received"
    )

    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When verification was processed"
    )

    processing_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Time taken to process webhook (milliseconds)"
    )

    # Error tracking
    error_message = models.TextField(
        blank=True,
        help_text="Error details if verification failed"
    )

    class Meta:
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['submission', '-received_at']),
            models.Index(fields=['hackathon', '-received_at']),
            models.Index(fields=['status', '-received_at']),
        ]

    def __str__(self):
        return f"{self.provider} verification for {self.submission} at {self.received_at}"
```

### 3.3 Migration Script

**File:** `synnovator/hackathons/migrations/XXXX_add_git_integration.py`

```python
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('hackathons', 'XXXX_previous_migration'),
    ]

    operations = [
        # Add Git fields to HackathonPage
        migrations.AddField(
            model_name='hackathonpage',
            name='git_repo_url',
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name='hackathonpage',
            name='git_branch',
            field=models.CharField(blank=True, default='main', max_length=100),
        ),
        # ... add all other fields ...

        # Create VerificationLog model
        migrations.CreateModel(
            name='VerificationLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('provider', models.CharField(max_length=50)),
                ('webhook_payload', models.JSONField()),
                # ... all other fields ...
            ],
        ),
    ]
```

---

## 4. Wagtail-to-Git Export

### 4.1 YAML Schema

**File:** `hackathon.yaml` (in Git repository)

```yaml
version: "1.0"

event:
  id: genai-sprint-2026
  name: "GenAI Sprint 2026"
  slug: genai-sprint-2026
  description: "Build innovative AI solutions in 48 hours"

  team:
    min_size: 2
    max_size: 5
    allow_solo: false
    required_roles:
      - hacker
      - hustler

phases:
  - id: registration
    title: "Registration"
    description: "Sign up and complete your profile"
    start_date: "2026-02-01T00:00:00Z"
    end_date: "2026-02-14T23:59:59Z"
    order: 1

  - id: team_formation
    title: "Team Formation"
    description: "Find your co-founders"
    start_date: "2026-02-01T00:00:00Z"
    end_date: "2026-02-15T23:59:59Z"
    order: 2

  - id: hacking
    title: "Hacking Period"
    description: "Build your AI solution"
    start_date: "2026-02-15T00:00:00Z"
    end_date: "2026-02-17T23:59:59Z"
    order: 3
    requirements:
      must_have_team: true
      submission_required: true

  - id: judging
    title: "Judging"
    description: "Present to judges and get feedback"
    start_date: "2026-02-17T00:00:00Z"
    end_date: "2026-02-19T23:59:59Z"
    order: 4

  - id: awards
    title: "Awards Ceremony"
    description: "Winners announced"
    start_date: "2026-02-19T18:00:00Z"
    end_date: "2026-02-19T20:00:00Z"
    order: 5

prizes:
  - id: grand_prize
    title: "Grand Prize"
    description: "Best overall solution"
    rank: 1
    monetary_value: 10000.00
    benefits:
      - "$10,000 cash"
      - "Incubation support"
      - "Mentorship from industry leaders"

  - id: runner_up
    title: "Runner Up"
    description: "Second place"
    rank: 2
    monetary_value: 5000.00

  - id: third_place
    title: "Third Place"
    description: "Third place"
    rank: 3
    monetary_value: 2500.00

scoring:
  passing_score: 80.0
  max_score: 100.0
  criteria:
    - name: "Technical Excellence"
      weight: 0.4
      description: "Code quality, architecture, innovation"
    - name: "Business Viability"
      weight: 0.3
      description: "Market fit, revenue potential"
    - name: "User Experience"
      weight: 0.3
      description: "Usability, design, documentation"
```

### 4.2 Export Logic

**File:** `synnovator/hackathons/git_sync.py`

```python
import yaml
from datetime import datetime
from decimal import Decimal

class GitConfigExporter:
    """
    Export HackathonPage configuration to YAML format.
    Used when COO wants to commit configuration to Git.
    """

    def __init__(self, hackathon_page):
        self.hackathon = hackathon_page

    def export_to_yaml(self):
        """
        Convert HackathonPage + Phase + Prize models to YAML dict.
        Returns dict (not YAML string) for flexibility.
        """
        data = {
            'version': '1.0',
            'event': {
                'id': self.hackathon.slug,
                'name': self.hackathon.title,
                'slug': self.hackathon.slug,
                'description': self.hackathon.description,
                'team': {
                    'min_size': self.hackathon.min_team_size,
                    'max_size': self.hackathon.max_team_size,
                    'allow_solo': self.hackathon.allow_solo,
                    'required_roles': self.hackathon.required_roles or [],
                }
            },
            'phases': self._export_phases(),
            'prizes': self._export_prizes(),
            'scoring': {
                'passing_score': float(self.hackathon.passing_score),
                'max_score': 100.0,
            }
        }

        return data

    def _export_phases(self):
        """Export all phases for this hackathon"""
        phases = []
        for phase in self.hackathon.phases.all().order_by('order'):
            phases.append({
                'id': f'phase_{phase.id}',
                'title': phase.title,
                'description': phase.description,
                'start_date': phase.start_date.isoformat(),
                'end_date': phase.end_date.isoformat(),
                'order': phase.order,
            })
        return phases

    def _export_prizes(self):
        """Export all prizes for this hackathon"""
        prizes = []
        for prize in self.hackathon.prizes.all().order_by('rank'):
            prize_data = {
                'id': f'prize_{prize.id}',
                'title': prize.title,
                'description': prize.description,
                'rank': prize.rank,
            }
            if prize.monetary_value:
                prize_data['monetary_value'] = float(prize.monetary_value)
            prizes.append(prize_data)
        return prizes

    def export_to_yaml_string(self):
        """Export to YAML string (for file writing)"""
        data = self.export_to_yaml()
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    def push_to_github(self, commit_message="Update hackathon configuration"):
        """
        Push configuration to GitHub repository.
        Requires github_token in settings or environment.
        """
        import requests
        from django.conf import settings

        if not self.hackathon.git_repo_url:
            raise ValueError("git_repo_url not configured")

        # Parse GitHub URL
        # Example: https://github.com/owner/repo
        parts = self.hackathon.git_repo_url.rstrip('/').split('/')
        owner, repo = parts[-2], parts[-1]

        # Get file contents
        yaml_content = self.export_to_yaml_string()

        # GitHub Contents API
        # https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{self.hackathon.git_config_path}"

        headers = {
            'Authorization': f'token {settings.GITHUB_API_TOKEN}',
            'Accept': 'application/vnd.github.v3+json',
        }

        # Get current file SHA (required for updates)
        response = requests.get(url, headers=headers, params={'ref': self.hackathon.git_branch})
        current_sha = response.json().get('sha') if response.status_code == 200 else None

        # Prepare payload
        import base64
        payload = {
            'message': commit_message,
            'content': base64.b64encode(yaml_content.encode('utf-8')).decode('utf-8'),
            'branch': self.hackathon.git_branch,
        }

        if current_sha:
            payload['sha'] = current_sha

        # Create/update file
        response = requests.put(url, headers=headers, json=payload)

        if response.status_code in [200, 201]:
            # Update last_sync fields
            from django.utils import timezone
            self.hackathon.last_sync_at = timezone.now()
            self.hackathon.last_sync_commit = response.json()['commit']['sha']
            self.hackathon.sync_status = 'success'
            self.hackathon.sync_error_message = ''
            self.hackathon.save()
            return response.json()
        else:
            self.hackathon.sync_status = 'failed'
            self.hackathon.sync_error_message = response.text
            self.hackathon.save()
            raise Exception(f"GitHub API error: {response.status_code} {response.text}")
```

---

## 5. Git-to-Wagtail Import

### 5.1 Import Logic

**File:** `synnovator/hackathons/git_sync.py` (continued)

```python
import requests
import yaml
from django.db import transaction
from django.utils import timezone

class GitConfigSyncer:
    """
    Sync hackathon configuration FROM Git TO Wagtail.

    This is the primary sync direction - Git is the source of truth.
    """

    def __init__(self, hackathon_page):
        self.hackathon = hackathon_page

    def fetch_yaml_from_git(self):
        """
        Fetch hackathon.yaml from GitHub/GitLab.
        Returns parsed YAML dict.
        """
        if not self.hackathon.git_repo_url:
            raise ValueError("git_repo_url not configured")

        # GitHub raw content URL
        # https://raw.githubusercontent.com/owner/repo/branch/path
        parts = self.hackathon.git_repo_url.rstrip('/').split('/')
        owner, repo = parts[-2], parts[-1]

        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{self.hackathon.git_branch}/{self.hackathon.git_config_path}"

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Parse YAML
        config = yaml.safe_load(response.text)
        return config

    @transaction.atomic
    def sync_from_git(self):
        """
        Sync configuration from Git to Wagtail models.

        Steps:
        1. Fetch YAML from Git
        2. Validate schema
        3. Update HackathonPage fields
        4. Update Phase models (create/update/delete)
        5. Update Prize models (create/update/delete)
        6. Record sync success
        """
        try:
            # Fetch configuration
            config = self.fetch_yaml_from_git()

            # Validate version
            if config.get('version') != '1.0':
                raise ValueError(f"Unsupported YAML version: {config.get('version')}")

            # Update HackathonPage fields
            event_data = config.get('event', {})
            team_config = event_data.get('team', {})

            self.hackathon.min_team_size = team_config.get('min_size', 2)
            self.hackathon.max_team_size = team_config.get('max_size', 5)
            self.hackathon.allow_solo = team_config.get('allow_solo', False)
            self.hackathon.required_roles = team_config.get('required_roles', [])

            scoring_config = config.get('scoring', {})
            self.hackathon.passing_score = scoring_config.get('passing_score', 80.0)

            # Sync phases
            self._sync_phases(config.get('phases', []))

            # Sync prizes
            self._sync_prizes(config.get('prizes', []))

            # Record success
            self.hackathon.last_sync_at = timezone.now()
            self.hackathon.sync_status = 'success'
            self.hackathon.sync_error_message = ''
            self.hackathon.save()

            return {
                'status': 'success',
                'phases_synced': len(config.get('phases', [])),
                'prizes_synced': len(config.get('prizes', [])),
            }

        except Exception as e:
            # Record failure
            self.hackathon.sync_status = 'failed'
            self.hackathon.sync_error_message = str(e)
            self.hackathon.save()
            raise

    def _sync_phases(self, phases_data):
        """
        Sync phases from YAML to Phase models.

        Strategy: Replace all phases (delete existing, create new).
        This avoids complex conflict resolution.
        """
        from .models import Phase
        from django.utils.dateparse import parse_datetime

        # Delete existing phases
        self.hackathon.phases.all().delete()

        # Create new phases
        for phase_data in phases_data:
            Phase.objects.create(
                hackathon=self.hackathon,
                title=phase_data['title'],
                description=phase_data.get('description', ''),
                start_date=parse_datetime(phase_data['start_date']),
                end_date=parse_datetime(phase_data['end_date']),
                order=phase_data.get('order', 0),
            )

    def _sync_prizes(self, prizes_data):
        """
        Sync prizes from YAML to Prize models.

        Strategy: Replace all prizes.
        """
        from .models import Prize
        from decimal import Decimal

        # Delete existing prizes
        self.hackathon.prizes.all().delete()

        # Create new prizes
        for prize_data in prizes_data:
            Prize.objects.create(
                hackathon=self.hackathon,
                title=prize_data['title'],
                description=prize_data.get('description', ''),
                rank=prize_data.get('rank', 1),
                monetary_value=Decimal(str(prize_data.get('monetary_value', 0))),
            )
```

### 5.2 Management Command

**File:** `synnovator/hackathons/management/commands/sync_hackathon_config.py`

```python
from django.core.management.base import BaseCommand
from synnovator.hackathons.models import HackathonPage
from synnovator.hackathons.git_sync import GitConfigSyncer

class Command(BaseCommand):
    help = 'Sync hackathon configuration from Git repository'

    def add_arguments(self, parser):
        parser.add_argument('hackathon_slug', type=str, help='Hackathon slug')
        parser.add_argument('--dry-run', action='store_true', help='Validate without saving')

    def handle(self, *args, **options):
        slug = options['hackathon_slug']
        dry_run = options.get('dry_run', False)

        try:
            hackathon = HackathonPage.objects.get(slug=slug)
        except HackathonPage.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Hackathon not found: {slug}'))
            return

        if not hackathon.git_repo_url:
            self.stdout.write(self.style.ERROR('git_repo_url not configured'))
            return

        self.stdout.write(f'Syncing {hackathon.title} from {hackathon.git_repo_url}...')

        syncer = GitConfigSyncer(hackathon)

        try:
            if dry_run:
                config = syncer.fetch_yaml_from_git()
                self.stdout.write(self.style.SUCCESS('✓ YAML validation passed'))
                self.stdout.write(f"  Phases: {len(config.get('phases', []))}")
                self.stdout.write(f"  Prizes: {len(config.get('prizes', []))}")
            else:
                result = syncer.sync_from_git()
                self.stdout.write(self.style.SUCCESS(f'✓ Sync completed'))
                self.stdout.write(f"  Phases synced: {result['phases_synced']}")
                self.stdout.write(f"  Prizes synced: {result['prizes_synced']}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Sync failed: {e}'))
```

**Usage:**
```bash
# Validate configuration
uv run python manage.py sync_hackathon_config genai-sprint-2026 --dry-run

# Sync from Git
uv run python manage.py sync_hackathon_config genai-sprint-2026
```

---

## 6. Webhook Verification System

### 6.1 Webhook Endpoint

**File:** `synnovator/hackathons/webhooks.py`

```python
import hmac
import hashlib
import json
import time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Submission, HackathonPage, VerificationLog

@csrf_exempt
@require_POST
def github_actions_webhook(request, submission_id):
    """
    Webhook endpoint for GitHub Actions verification results.

    Expected payload:
    {
        "submission_id": 123,
        "status": "success",
        "score": 95.5,
        "test_results": {
            "passed": 10,
            "failed": 0,
            "skipped": 0
        },
        "logs": "Test output...",
        "metadata": {
            "run_id": "123456",
            "commit_sha": "abc123"
        }
    }

    Headers:
    - X-Hub-Signature-256: sha256=<hmac>
    """
    start_time = time.time()

    try:
        # Get submission
        submission = get_object_or_404(Submission, id=submission_id)
        hackathon = submission.hackathon or submission.quest.hackathon

        # Verify HMAC signature
        signature = request.headers.get('X-Hub-Signature-256', '')
        if not verify_hmac_signature(
            request.body,
            hackathon.webhook_secret,
            signature
        ):
            # Log failed verification
            VerificationLog.objects.create(
                submission=submission,
                hackathon=hackathon,
                provider='github_actions',
                webhook_payload=json.loads(request.body),
                signature_verified=False,
                status='error',
                error_message='Invalid HMAC signature',
            )
            return JsonResponse({'error': 'Invalid signature'}, status=403)

        # Parse payload
        payload = json.loads(request.body)

        # Process verification result
        with transaction.atomic():
            result = process_verification_result(submission, payload)

            # Create verification log
            processing_time = int((time.time() - start_time) * 1000)
            VerificationLog.objects.create(
                submission=submission,
                hackathon=hackathon,
                provider='github_actions',
                webhook_payload=payload,
                signature_verified=True,
                status=result['status'],
                score=result.get('score'),
                test_results=result.get('test_results', {}),
                logs=result.get('logs', ''),
                processed_at=timezone.now(),
                processing_time_ms=processing_time,
            )

        return JsonResponse({
            'status': 'success',
            'submission_id': submission.id,
            'processing_time_ms': processing_time,
        })

    except Submission.DoesNotExist:
        return JsonResponse({'error': 'Submission not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def verify_hmac_signature(payload_body, secret, signature):
    """
    Verify HMAC SHA-256 signature from GitHub/GitLab webhook.

    Args:
        payload_body: Raw request body (bytes)
        secret: Webhook secret string
        signature: Signature from X-Hub-Signature-256 header (e.g., "sha256=abc123")

    Returns:
        bool: True if signature is valid
    """
    if not signature.startswith('sha256='):
        return False

    provided_sig = signature.replace('sha256=', '')

    expected_sig = hmac.new(
        key=secret.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_sig, provided_sig)


def process_verification_result(submission, payload):
    """
    Process verification result and update submission.

    Args:
        submission: Submission instance
        payload: Webhook payload dict

    Returns:
        dict: Processing result
    """
    from django.utils import timezone

    status = payload.get('status')  # 'success', 'failed', 'error'
    score = payload.get('score')
    test_results = payload.get('test_results', {})
    logs = payload.get('logs', '')

    # Update submission
    if status == 'success':
        submission.verification_status = 'verified'
        submission.score = score
        submission.verified_at = timezone.now()

        # Award XP if quest submission and score >= passing_score
        if submission.quest and submission.user:
            if score >= submission.quest.passing_score:
                submission.user.award_xp(
                    submission.quest.xp_reward,
                    reason=f"Completed quest: {submission.quest.title}"
                )

        # Update team score if hackathon submission
        if submission.hackathon and submission.team:
            submission.team.final_score = score
            submission.team.status = 'verified'
            submission.team.save()

    elif status == 'failed':
        submission.verification_status = 'rejected'
        submission.feedback = f"Verification failed:\n{logs}"

    submission.save()

    return {
        'status': status,
        'score': score,
        'test_results': test_results,
        'logs': logs,
    }
```

### 6.2 URL Configuration

**File:** `synnovator/urls.py`

```python
from django.urls import path
from synnovator.hackathons import webhooks

urlpatterns = [
    # ... existing URLs ...

    # Webhook endpoints
    path(
        'api/webhooks/verification/<int:submission_id>/',
        webhooks.github_actions_webhook,
        name='webhook_verification'
    ),
]
```

### 6.3 GitHub Actions Workflow Example

**File:** `.github/workflows/verify-submission.yml` (in participant's repository)

```yaml
name: Synnovator Verification

on:
  push:
    branches: [main, master]
  workflow_dispatch:
    inputs:
      submission_id:
        description: 'Synnovator Submission ID'
        required: true

jobs:
  verify:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        id: tests
        run: |
          pytest --cov --cov-report=json
          echo "SCORE=$(python calculate_score.py)" >> $GITHUB_OUTPUT

      - name: Send results to Synnovator
        if: always()
        env:
          WEBHOOK_SECRET: ${{ secrets.SYNNOVATOR_WEBHOOK_SECRET }}
          SUBMISSION_ID: ${{ github.event.inputs.submission_id }}
        run: |
          python .github/scripts/send_webhook.py \
            --submission-id $SUBMISSION_ID \
            --status ${{ steps.tests.outcome }} \
            --score ${{ steps.tests.outputs.SCORE }}
```

**File:** `.github/scripts/send_webhook.py`

```python
#!/usr/bin/env python3
import os
import sys
import json
import hmac
import hashlib
import requests
import argparse

def send_webhook(submission_id, status, score, logs=''):
    """Send verification result to Synnovator webhook"""
    webhook_url = f"https://synnovator.com/api/webhooks/verification/{submission_id}/"
    webhook_secret = os.environ['WEBHOOK_SECRET']

    payload = {
        'submission_id': submission_id,
        'status': status,
        'score': score,
        'logs': logs,
        'metadata': {
            'run_id': os.environ.get('GITHUB_RUN_ID'),
            'commit_sha': os.environ.get('GITHUB_SHA'),
        }
    }

    payload_bytes = json.dumps(payload).encode('utf-8')

    # Calculate HMAC signature
    signature = hmac.new(
        webhook_secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()

    headers = {
        'Content-Type': 'application/json',
        'X-Hub-Signature-256': f'sha256={signature}',
    }

    response = requests.post(webhook_url, data=payload_bytes, headers=headers)
    response.raise_for_status()

    print(f"✓ Webhook sent successfully: {response.status_code}")
    return response.json()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--submission-id', required=True, type=int)
    parser.add_argument('--status', required=True, choices=['success', 'failed'])
    parser.add_argument('--score', type=float, default=0)
    args = parser.parse_args()

    send_webhook(args.submission_id, args.status, args.score)
```

---

## 7. Security Implementation

### 7.1 HMAC Signature Verification

**Why HMAC?**
- Prevents unauthorized score manipulation
- Ensures webhook came from trusted CI/CD system
- Detects payload tampering

**Implementation:**
```python
def verify_hmac_signature(payload_body, secret, signature):
    """
    GitHub/GitLab use HMAC SHA-256 with format:
    X-Hub-Signature-256: sha256=<hex_digest>
    """
    if not signature.startswith('sha256='):
        return False

    provided_sig = signature.replace('sha256=', '')

    expected_sig = hmac.new(
        key=secret.encode('utf-8'),
        msg=payload_body,  # Must be raw bytes, not JSON
        digestmod=hashlib.sha256
    ).hexdigest()

    # Constant-time comparison prevents timing attacks
    return hmac.compare_digest(expected_sig, provided_sig)
```

**Key Security Points:**
1. **Use raw request body** - Don't parse JSON first
2. **Constant-time comparison** - Use `hmac.compare_digest()`
3. **Auto-generate secrets** - Use `secrets.token_urlsafe(32)`
4. **Store securely** - Consider encrypting webhook_secret field

### 7.2 IP Whitelisting (Optional)

**File:** `synnovator/hackathons/webhooks.py`

```python
# GitHub Actions IP ranges (as of 2026-01)
ALLOWED_WEBHOOK_IPS = [
    '140.82.112.0/20',  # GitHub
    '143.55.64.0/20',   # GitHub
    '185.199.108.0/22', # GitHub
    # Add GitLab CI ranges if using GitLab
]

def is_ip_allowed(request):
    """Check if request IP is from allowed CI/CD provider"""
    import ipaddress

    client_ip = request.META.get('REMOTE_ADDR')

    for ip_range in ALLOWED_WEBHOOK_IPS:
        if ipaddress.ip_address(client_ip) in ipaddress.ip_network(ip_range):
            return True

    return False

@csrf_exempt
@require_POST
def github_actions_webhook(request, submission_id):
    # Optional: Check IP first (before HMAC verification)
    if not is_ip_allowed(request):
        return JsonResponse({'error': 'IP not allowed'}, status=403)

    # ... rest of webhook handling ...
```

**Note:** IP whitelisting is optional and adds complexity. HMAC signature verification is sufficient for most use cases.

### 7.3 Rate Limiting

**File:** `synnovator/settings/base.py`

```python
# Django Ratelimit (pip install django-ratelimit)
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'
```

**File:** `synnovator/hackathons/webhooks.py`

```python
from django_ratelimit.decorators import ratelimit

@csrf_exempt
@require_POST
@ratelimit(key='ip', rate='60/h', method='POST')  # Max 60 webhooks per hour per IP
def github_actions_webhook(request, submission_id):
    # ... webhook handling ...
```

### 7.4 Payload Size Limits

```python
from django.conf import settings

# settings/base.py
MAX_WEBHOOK_PAYLOAD_SIZE = 1 * 1024 * 1024  # 1 MB

@csrf_exempt
@require_POST
def github_actions_webhook(request, submission_id):
    # Check payload size
    if len(request.body) > settings.MAX_WEBHOOK_PAYLOAD_SIZE:
        return JsonResponse({'error': 'Payload too large'}, status=413)

    # ... rest of webhook handling ...
```

---

## 8. Migration Strategy

### 8.1 Migration Steps

**Step 1: Deploy Code (Feature Flag Disabled)**

```python
# settings/base.py
HACKATHON_GIT_INTEGRATION_ENABLED = False
```

Deploy all Git integration code but keep feature flag disabled. This allows gradual rollout and easy rollback.

**Step 2: Test on Staging Hackathon**

1. Create test hackathon in staging environment
2. Configure Git repository
3. Test YAML sync (both directions)
4. Test webhook endpoint with dummy payloads
5. Verify HMAC signature validation
6. Test error handling (invalid YAML, network errors)

**Step 3: Enable for Pilot Hackathon**

```python
# Enable per-hackathon
class HackathonPage(Page):
    git_integration_enabled = models.BooleanField(default=False)
```

Enable Git integration for ONE production hackathon as pilot:
- Choose low-stakes event (< 50 participants)
- Monitor webhook logs closely
- Keep manual verification as fallback
- Gather feedback from COO

**Step 4: Gradual Rollout**

After successful pilot:
- Enable for additional hackathons one at a time
- Document common issues and solutions
- Train COO on Git sync workflow
- Build runbook for troubleshooting

**Step 5: Full Rollout**

```python
# settings/base.py
HACKATHON_GIT_INTEGRATION_ENABLED = True
```

Enable globally once:
- 5+ successful hackathons using Git integration
- < 1% webhook error rate
- COO comfortable with Git workflow
- All edge cases documented

### 8.2 Backward Compatibility

**Ensure manual verification still works:**

```python
def process_submission(submission):
    """
    Process submission using either:
    1. Automated webhook (if git_integration_enabled)
    2. Manual verification (fallback)
    """
    hackathon = submission.hackathon or submission.quest.hackathon

    if hackathon.git_integration_enabled and hackathon.verification_provider:
        # Wait for webhook
        submission.verification_status = 'pending_webhook'
    else:
        # Manual verification workflow (MVP)
        submission.verification_status = 'pending'

    submission.save()
```

**Admin interface shows both options:**

```python
# Wagtail admin
class SubmissionAdmin(ModelAdmin):
    list_display = [
        'get_submitter',
        'get_verification_method',  # "Manual" or "Automated (GitHub Actions)"
        'verification_status',
        'score',
    ]
```

### 8.3 Rollback Plan

**If Git integration fails:**

1. **Disable feature flag:**
   ```python
   HACKATHON_GIT_INTEGRATION_ENABLED = False
   ```

2. **Switch hackathon to manual verification:**
   ```python
   hackathon.git_integration_enabled = False
   hackathon.save()
   ```

3. **All pending submissions revert to manual review:**
   ```python
   Submission.objects.filter(
       verification_status='pending_webhook'
   ).update(verification_status='pending')
   ```

4. **COO reviews submissions normally in Wagtail admin**

**No data loss** - VerificationLog keeps complete audit trail of all webhook attempts.

---

## 9. Dependencies

### 9.1 Backend Dependencies

**File:** `pyproject.toml`

```toml
[project]
dependencies = [
    # ... existing Wagtail/Django dependencies ...

    # Phase 3: Git Integration
    "PyYAML>=6.0.1",          # YAML parsing
    "requests>=2.31.0",       # GitHub/GitLab API calls
    "gitpython>=3.1.40",      # Git operations (optional, for local cloning)
    "cryptography>=42.0.0",   # Webhook secret encryption

    # Phase 3: Async Tasks
    "celery>=5.3.4",          # Background jobs
    "redis>=5.0.1",           # Celery broker + caching

    # Phase 3: REST API
    "djangorestframework>=3.14.0",
    "djangorestframework-simplejwt>=5.3.1",
    "drf-spectacular>=0.27.0",  # API documentation

    # Phase 3: Monitoring
    "sentry-sdk>=1.40.0",     # Error tracking
]
```

### 9.2 Infrastructure Requirements

**Phase 3 Infrastructure:**

1. **Redis:**
   - Celery broker
   - Leaderboard caching
   - Session storage

   ```bash
   # Docker Compose
   redis:
     image: redis:7-alpine
     ports:
       - "6379:6379"
     volumes:
       - redis_data:/data
   ```

2. **Celery Workers:**
   ```bash
   # Start Celery worker
   uv run celery -A synnovator worker -l info

   # Start Celery beat (periodic tasks)
   uv run celery -A synnovator beat -l info
   ```

3. **Webhook Monitoring:**
   - Use Sentry for error tracking
   - Set up alerts for webhook failures
   - Monitor VerificationLog table for anomalies

### 9.3 Environment Variables

**File:** `.env.production`

```bash
# Git Integration
GITHUB_API_TOKEN=ghp_xxxxxxxxxxxxx  # For GitHub API access
GITLAB_API_TOKEN=glpat-xxxxxxxxxxxxx  # For GitLab API access

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Webhook Security
WEBHOOK_IP_WHITELIST_ENABLED=false  # Set true to enable IP whitelisting

# Monitoring
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
```

---

## 10. Implementation Checklist

### 10.1 Phase 3 Implementation Checklist

**Models & Database:**
- [ ] Add Git fields to HackathonPage model
- [ ] Create VerificationLog model
- [ ] Create and run migrations
- [ ] Test migrations on staging database
- [ ] Add indexes for VerificationLog queries

**Git Sync:**
- [ ] Implement GitConfigExporter class
- [ ] Implement GitConfigSyncer class
- [ ] Write YAML schema documentation
- [ ] Create management command: `sync_hackathon_config`
- [ ] Test sync with sample Git repository
- [ ] Handle YAML validation errors gracefully
- [ ] Test network failure scenarios

**Webhooks:**
- [ ] Create webhook endpoint view
- [ ] Implement HMAC signature verification
- [ ] Add webhook URL to Django urls.py
- [ ] Test webhook with curl/Postman
- [ ] Test invalid signature rejection
- [ ] Test payload validation

**Celery Integration:**
- [ ] Set up Redis for Celery
- [ ] Create Celery tasks for Git sync
- [ ] Create Celery tasks for webhook processing
- [ ] Test async task execution
- [ ] Monitor Celery worker health

**Security:**
- [ ] Generate webhook secrets automatically
- [ ] Store secrets securely (consider encryption)
- [ ] Implement rate limiting on webhook endpoint
- [ ] Test HMAC verification with all providers
- [ ] Optional: Implement IP whitelisting
- [ ] Security audit by external reviewer

**Testing:**
- [ ] Write unit tests for GitConfigSyncer
- [ ] Write unit tests for GitConfigExporter
- [ ] Write unit tests for HMAC verification
- [ ] Write integration tests for webhook endpoint
- [ ] Test with real GitHub Actions workflow
- [ ] Test error scenarios (invalid YAML, network errors, etc.)
- [ ] Load testing: 100+ concurrent webhooks

**Documentation:**
- [ ] Document YAML schema for participants
- [ ] Create GitHub Actions workflow template
- [ ] Write COO guide for Git sync
- [ ] Create troubleshooting runbook
- [ ] Document rollback procedures
- [ ] API documentation for webhook endpoint

**Deployment:**
- [ ] Deploy with feature flag disabled
- [ ] Test on staging environment
- [ ] Enable for pilot hackathon
- [ ] Monitor logs and metrics
- [ ] Gather feedback from COO
- [ ] Gradual rollout to production
- [ ] Update CLAUDE.md with Git workflow

---

## 11. Testing Guide

### 11.1 Unit Tests

**File:** `synnovator/hackathons/tests/test_git_sync.py`

```python
import pytest
from django.test import TestCase
from unittest.mock import patch, Mock
from synnovator.hackathons.git_sync import GitConfigSyncer, GitConfigExporter
from synnovator.hackathons.models import HackathonPage, Phase, Prize

class GitConfigExporterTest(TestCase):
    def setUp(self):
        self.hackathon = HackathonPage.objects.create(
            title="Test Hackathon",
            slug="test-hackathon",
            min_team_size=2,
            max_team_size=5,
        )

        # Create phases
        Phase.objects.create(
            hackathon=self.hackathon,
            title="Registration",
            start_date="2026-02-01T00:00:00Z",
            end_date="2026-02-14T23:59:59Z",
            order=1,
        )

        # Create prizes
        Prize.objects.create(
            hackathon=self.hackathon,
            title="First Place",
            rank=1,
            monetary_value=10000,
        )

    def test_export_to_yaml(self):
        exporter = GitConfigExporter(self.hackathon)
        data = exporter.export_to_yaml()

        assert data['version'] == '1.0'
        assert data['event']['name'] == "Test Hackathon"
        assert len(data['phases']) == 1
        assert len(data['prizes']) == 1
        assert data['phases'][0]['title'] == "Registration"
        assert data['prizes'][0]['monetary_value'] == 10000.0

    def test_export_to_yaml_string(self):
        exporter = GitConfigExporter(self.hackathon)
        yaml_str = exporter.export_to_yaml_string()

        assert 'version: "1.0"' in yaml_str
        assert 'Test Hackathon' in yaml_str


class GitConfigSyncerTest(TestCase):
    def setUp(self):
        self.hackathon = HackathonPage.objects.create(
            title="Test Hackathon",
            slug="test-hackathon",
            git_repo_url="https://github.com/test/repo",
            git_branch="main",
        )

    @patch('requests.get')
    def test_fetch_yaml_from_git(self, mock_get):
        mock_get.return_value = Mock(
            status_code=200,
            text="""
version: "1.0"
event:
  name: "Test Hackathon"
phases:
  - title: "Registration"
    start_date: "2026-02-01T00:00:00Z"
    end_date: "2026-02-14T23:59:59Z"
prizes: []
            """
        )

        syncer = GitConfigSyncer(self.hackathon)
        config = syncer.fetch_yaml_from_git()

        assert config['version'] == '1.0'
        assert config['event']['name'] == "Test Hackathon"
        assert len(config['phases']) == 1

    @patch.object(GitConfigSyncer, 'fetch_yaml_from_git')
    def test_sync_from_git(self, mock_fetch):
        mock_fetch.return_value = {
            'version': '1.0',
            'event': {
                'team': {
                    'min_size': 3,
                    'max_size': 6,
                }
            },
            'phases': [
                {
                    'title': 'Registration',
                    'start_date': '2026-02-01T00:00:00Z',
                    'end_date': '2026-02-14T23:59:59Z',
                    'order': 1,
                }
            ],
            'prizes': [],
            'scoring': {'passing_score': 85.0}
        }

        syncer = GitConfigSyncer(self.hackathon)
        result = syncer.sync_from_git()

        self.hackathon.refresh_from_db()
        assert self.hackathon.min_team_size == 3
        assert self.hackathon.max_team_size == 6
        assert self.hackathon.passing_score == 85.0
        assert self.hackathon.phases.count() == 1
        assert self.hackathon.sync_status == 'success'
```

### 11.2 Webhook Tests

**File:** `synnovator/hackathons/tests/test_webhooks.py`

```python
import json
import hmac
import hashlib
from django.test import TestCase, Client
from django.urls import reverse
from synnovator.hackathons.models import Submission, HackathonPage, Quest, User

class WebhookTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('testuser')

        self.hackathon = HackathonPage.objects.create(
            title="Test Hackathon",
            slug="test-hackathon",
            webhook_secret="test_secret_key",
            verification_provider="github_actions",
        )

        self.quest = Quest.objects.create(
            title="Test Quest",
            hackathon=self.hackathon,
            xp_reward=100,
            passing_score=80,
        )

        self.submission = Submission.objects.create(
            user=self.user,
            quest=self.quest,
            verification_status='pending',
        )

    def _sign_payload(self, payload, secret):
        """Generate HMAC signature for payload"""
        payload_bytes = json.dumps(payload).encode('utf-8')
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    def test_valid_webhook(self):
        payload = {
            'submission_id': self.submission.id,
            'status': 'success',
            'score': 95.5,
            'test_results': {'passed': 10, 'failed': 0},
        }

        signature = self._sign_payload(payload, self.hackathon.webhook_secret)

        response = self.client.post(
            reverse('webhook_verification', args=[self.submission.id]),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_HUB_SIGNATURE_256=signature,
        )

        assert response.status_code == 200

        self.submission.refresh_from_db()
        assert self.submission.verification_status == 'verified'
        assert self.submission.score == 95.5

    def test_invalid_signature(self):
        payload = {
            'submission_id': self.submission.id,
            'status': 'success',
            'score': 95.5,
        }

        response = self.client.post(
            reverse('webhook_verification', args=[self.submission.id]),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_HUB_SIGNATURE_256='sha256=invalid_signature',
        )

        assert response.status_code == 403
        assert response.json()['error'] == 'Invalid signature'

        # Submission should not be updated
        self.submission.refresh_from_db()
        assert self.submission.verification_status == 'pending'

    def test_failed_verification(self):
        payload = {
            'submission_id': self.submission.id,
            'status': 'failed',
            'score': 0,
            'logs': 'Tests failed: 5 passed, 5 failed',
        }

        signature = self._sign_payload(payload, self.hackathon.webhook_secret)

        response = self.client.post(
            reverse('webhook_verification', args=[self.submission.id]),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_HUB_SIGNATURE_256=signature,
        )

        assert response.status_code == 200

        self.submission.refresh_from_db()
        assert self.submission.verification_status == 'rejected'
        assert 'Tests failed' in self.submission.feedback
```

### 11.3 Load Testing

**File:** `load_test_webhooks.py`

```python
#!/usr/bin/env python3
"""
Load test webhook endpoint with 100+ concurrent requests.
Requires: pip install locust
Run: locust -f load_test_webhooks.py --host=https://staging.synnovator.com
"""
from locust import HttpUser, task, between
import json
import hmac
import hashlib

class WebhookUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.submission_id = 123  # Use test submission
        self.webhook_secret = "test_secret"

    def _sign_payload(self, payload):
        payload_bytes = json.dumps(payload).encode('utf-8')
        signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    @task
    def send_webhook(self):
        payload = {
            'submission_id': self.submission_id,
            'status': 'success',
            'score': 95.5,
        }

        signature = self._sign_payload(payload)

        self.client.post(
            f"/api/webhooks/verification/{self.submission_id}/",
            json=payload,
            headers={'X-Hub-Signature-256': signature},
        )
```

**Run load test:**
```bash
locust -f load_test_webhooks.py --host=https://staging.synnovator.com --users 100 --spawn-rate 10
```

**Success criteria:**
- All requests return 200 OK
- < 1% error rate
- Average response time < 500ms
- No database deadlocks

---

## 12. Troubleshooting

### 12.1 Common Issues

**Issue: Git sync fails with 404**

**Symptoms:**
- Error message: "GitHub API error: 404 Not Found"
- sync_status = 'failed'

**Solution:**
1. Check git_repo_url is correct
2. Verify repository is public OR GitHub token has access
3. Verify git_branch exists
4. Check git_config_path points to valid file

**Issue: Webhook signature verification fails**

**Symptoms:**
- Error: "Invalid signature"
- VerificationLog shows signature_verified=False

**Solution:**
1. Verify webhook_secret matches secret in GitHub Actions
2. Check signature header format: `sha256=<hex>`
3. Ensure raw request body is used (not parsed JSON)
4. Test with sample payload locally:
   ```python
   import hmac, hashlib, json
   payload = json.dumps({'test': 'data'}).encode('utf-8')
   secret = 'your_webhook_secret'
   sig = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()
   print(f"sha256={sig}")
   ```

**Issue: XP not awarded after verification**

**Symptoms:**
- Submission verified
- Score >= passing_score
- User XP unchanged

**Solution:**
1. Check `process_verification_result()` function runs
2. Verify `submission.quest` is set (not just hackathon)
3. Check `user.award_xp()` method implementation
4. Look for errors in logs

**Issue: Celery tasks not processing**

**Symptoms:**
- Git sync queued but never completes
- Tasks stuck in pending state

**Solution:**
1. Check Celery worker is running:
   ```bash
   ps aux | grep celery
   ```
2. Check Redis connection:
   ```bash
   redis-cli ping
   ```
3. Check Celery logs:
   ```bash
   tail -f celery.log
   ```
4. Restart Celery worker:
   ```bash
   pkill celery
   uv run celery -A synnovator worker -l info
   ```

### 12.2 Debugging Commands

**Check Git sync status:**
```bash
uv run python manage.py shell
>>> from synnovator.hackathons.models import HackathonPage
>>> h = HackathonPage.objects.get(slug='genai-sprint-2026')
>>> print(f"Status: {h.sync_status}")
>>> print(f"Last sync: {h.last_sync_at}")
>>> print(f"Error: {h.sync_error_message}")
```

**Test webhook signature locally:**
```python
from synnovator.hackathons.webhooks import verify_hmac_signature

payload = b'{"test": "data"}'
secret = "your_webhook_secret"
signature = "sha256=abc123..."  # From failed request

is_valid = verify_hmac_signature(payload, secret, signature)
print(f"Signature valid: {is_valid}")
```

**Check verification logs:**
```bash
uv run python manage.py shell
>>> from synnovator.hackathons.models import VerificationLog
>>> logs = VerificationLog.objects.filter(
...     signature_verified=False
... ).order_by('-received_at')[:10]
>>> for log in logs:
...     print(f"{log.received_at}: {log.error_message}")
```

### 12.3 Monitoring & Alerts

**Set up monitoring:**

1. **Sentry for errors:**
   ```python
   # settings/production.py
   import sentry_sdk
   sentry_sdk.init(
       dsn=os.environ['SENTRY_DSN'],
       environment='production',
   )
   ```

2. **Webhook success rate:**
   ```sql
   -- Check webhook success rate (last 24h)
   SELECT
       status,
       COUNT(*) as count,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
   FROM verification_log
   WHERE received_at >= NOW() - INTERVAL '24 hours'
   GROUP BY status;
   ```

3. **Alert on high failure rate:**
   - Set up alert if webhook error rate > 5%
   - Alert if Git sync fails 3+ times in a row
   - Alert if Celery queue depth > 100

---

## 13. Summary

### 13.1 Key Takeaways

✅ **Git integration is a Phase 3 enhancement, not MVP**
- MVP uses Wagtail CMS + manual verification
- Add Git integration only when scale requires it (> 100 participants)

✅ **Bidirectional sync requires careful design**
- Git is source of truth for configuration
- YAML schema must be versioned and validated
- Handle sync conflicts gracefully

✅ **Webhook security is critical**
- HMAC SHA-256 signature verification prevents manipulation
- Store complete audit trail in VerificationLog
- Rate limiting and payload size limits prevent abuse

✅ **Gradual rollout reduces risk**
- Deploy with feature flag disabled
- Test thoroughly on staging
- Enable for pilot hackathon first
- Keep manual verification as fallback

### 13.2 When NOT to Implement

**Skip Git integration if:**
- Platform has < 100 participants per event
- Manual verification is working well
- Team lacks DevOps expertise
- MVP hasn't been validated yet
- Budget/timeline is constrained

**Remember:** MVP delivers value in 4-6 weeks. Git integration adds 6-8 weeks. Don't over-engineer!

### 13.3 Next Steps After Implementation

Once Git integration is stable:

1. **REST API (Phase 3)**
   - Expose webhook endpoints as REST API
   - Allow external integrations
   - Document API with drf-spectacular

2. **Advanced Features (Phase 4)**
   - Multi-repository support
   - GitLab CI / Jenkins integration
   - Custom verification scripts
   - Real-time leaderboard updates via WebSocket

3. **Analytics Dashboard (Phase 4)**
   - Git sync metrics
   - Webhook success rates
   - Verification processing times
   - Team contribution graphs

---

**Document Version:** 1.0
**Last Updated:** 2026-01-20
**Status:** Ready for Phase 3 Implementation
**Estimated Implementation Time:** 6-8 weeks with 2 engineers

---

**END OF DOCUMENT**

For questions or clarifications, refer to:
- Main specification: `spec/refactor/README.md`
- Security: `spec/refactor/section-10.md`
- Critical files: `spec/refactor/section-09.md`
