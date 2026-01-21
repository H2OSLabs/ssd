## Section 7: Migration Strategy

### 7.1 Data Migration Plan

#### 7.1.1 User Model Migration

**Step 1: Add new fields to User model**

```python
# synnovator/users/migrations/0002_add_hackathon_fields.py
from django.db import migrations, models
import django.contrib.postgres.fields

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='github_username',
            field=models.CharField(max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='gitlab_username',
            field=models.CharField(max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='preferred_role',
            field=models.CharField(max_length=50, blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='skills',
            field=models.JSONField(default=list, blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='xp_points',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='reputation_score',
            field=models.DecimalField(max_digits=6, decimal_places=2, default=0.0),
        ),
        migrations.AddField(
            model_name='user',
            name='level',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='user',
            name='profile_completed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='is_seeking_team',
            field=models.BooleanField(default=False),
        ),
    ]
```

**Step 2: Prompt existing users to complete profile**

```python
# Post-migration task: Send email to existing users
from django.core.management.base import BaseCommand
from synnovator.users.models import User

class Command(BaseCommand):
    def handle(self, *args, **options):
        users_to_update = User.objects.filter(profile_completed=False)
        for user in users_to_update:
            # Send email with profile completion link
            send_profile_completion_email(user)
```

#### 7.1.2 EventPage to HackathonPage Migration

**Step 1: Create HackathonPage model (new app)**

```python
# synnovator/hackathons/migrations/0001_initial.py
# Creates HackathonPage, HackathonConfig, Phase, Prize, Team, etc.
```

**Step 2: Data migration for existing EventPage records**

```python
# synnovator/hackathons/migrations/0002_migrate_event_pages.py
from django.db import migrations

def migrate_event_pages(apps, schema_editor):
    """
    Convert EventPage records with category='hackathon' to HackathonPage.
    """
    EventPage = apps.get_model('events', 'EventPage')  # Assuming events app exists
    HackathonPage = apps.get_model('hackathons', 'HackathonPage')

    hackathon_events = EventPage.objects.filter(
        category='hackathon'  # Adjust field name if different
    )

    for event in hackathon_events:
        # Create HackathonPage with same parent and position
        hackathon = HackathonPage(
            title=event.title,
            slug=event.slug,
            description=event.body,  # Map description field
            status='archived',  # Mark as archived
            # Copy Wagtail page fields
            depth=event.depth,
            path=event.path,
            # ... copy other fields
        )
        hackathon.save()

        # Optionally: Delete old EventPage or keep for reference
        # event.delete()

def reverse_migration(apps, schema_editor):
    """Reverse migration - optional"""
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('hackathons', '0001_initial'),
        ('events', '0001_initial'),  # Adjust to actual events app migration
    ]

    operations = [
        migrations.RunPython(migrate_event_pages, reverse_migration),
    ]
```

#### 7.1.3 EventParticipant to Team/TeamMember Migration

**Step 1: Migrate team data**

```python
# synnovator/hackathons/migrations/0003_migrate_participants.py
from django.db import migrations
from collections import defaultdict

def migrate_participants(apps, schema_editor):
    """
    Group EventParticipant records by team_name and convert to Team + TeamMember.
    """
    EventParticipant = apps.get_model('events', 'EventParticipant')
    HackathonPage = apps.get_model('hackathons', 'HackathonPage')
    Team = apps.get_model('hackathons', 'Team')
    TeamMember = apps.get_model('hackathons', 'TeamMember')

    # Get all participants grouped by event and team_name
    participants = EventParticipant.objects.all()
    teams_data = defaultdict(list)

    for participant in participants:
        key = (participant.event_id, participant.team_name)
        teams_data[key].append(participant)

    # Create Team records
    for (event_id, team_name), members in teams_data.items():
        # Find corresponding HackathonPage
        try:
            hackathon = HackathonPage.objects.get(pk=event_id)
        except HackathonPage.DoesNotExist:
            continue

        # Create Team
        team = Team.objects.create(
            hackathon=hackathon,
            name=team_name,
            slug=slugify(team_name),
            status='forming',
        )

        # Create TeamMember records
        for i, member_data in enumerate(members):
            TeamMember.objects.create(
                team=team,
                user_id=member_data.user_id,
                role=member_data.role if hasattr(member_data, 'role') else 'hacker',
                is_leader=(i == 0),  # First member is leader
            )

class Migration(migrations.Migration):
    dependencies = [
        ('hackathons', '0002_migrate_event_pages'),
    ]

    operations = [
        migrations.RunPython(migrate_participants),
    ]
```

### 7.2 Backward Compatibility

#### 7.2.1 URL Redirects

```python
# synnovator/urls.py
from django.urls import path, re_path
from django.views.generic import RedirectView

urlpatterns = [
    # Redirect old event URLs to hackathon URLs
    re_path(
        r'^events/(?P<slug>[\w-]+)/$',
        RedirectView.as_view(pattern_name='hackathons:detail', permanent=True)
    ),
    re_path(
        r'^events/$',
        RedirectView.as_view(pattern_name='hackathons:listing', permanent=True)
    ),
]
```

#### 7.2.2 Keep Old Models (Optional)

**If you want to keep EventPage for non-hackathon events:**

```python
# synnovator/events/models.py - Keep unchanged
class EventPage(Page):
    # Existing implementation for workshops, meetups, etc.
    pass
```

### 7.3 Migration Execution Order

1. **Backup database**
   ```bash
   uv run python manage.py dumpdata > backup_before_refactor.json
   ```

2. **Run migrations in order:**
   ```bash
   # User model extensions
   uv run python manage.py migrate users 0002_add_hackathon_fields

   # Create hackathons app
   uv run python manage.py migrate hackathons 0001_initial

   # Migrate data
   uv run python manage.py migrate hackathons 0002_migrate_event_pages
   uv run python manage.py migrate hackathons 0003_migrate_participants

   # Run all remaining migrations
   uv run python manage.py migrate
   ```

3. **Verify migration:**
   ```bash
   uv run python manage.py shell
   >>> from synnovator.hackathons.models import HackathonPage, Team
   >>> HackathonPage.objects.count()
   >>> Team.objects.count()
   ```

4. **Test admin interface:**
   - Visit `/admin/`
   - Check that HackathonPage appears
   - Verify phases and prizes display correctly

### 7.4 Rollback Plan

**If migration fails:**

1. **Restore database from backup**
   ```bash
   # Restore PostgreSQL
   pg_restore -d synnovator backup.dump

   # Or restore from JSON
   uv run python manage.py loaddata backup_before_refactor.json
   ```

2. **Revert migrations**
   ```bash
   uv run python manage.py migrate hackathons zero
   uv run python manage.py migrate users 0001_initial
   ```

3. **Remove hackathons app from INSTALLED_APPS**

---

