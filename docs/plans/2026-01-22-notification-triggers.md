# Notification System Triggers Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement notification triggers so admin sees a "login successful" notification and receives new hackathon creation alerts.

**Architecture:** Use Django's `user_logged_in` signal for login notifications and Wagtail's `page_published` signal for hackathon creation notifications. Register signals in the notifications app's `ready()` method. Add a new notification type `hackathon_created`.

**Tech Stack:** Django signals, Wagtail signals, existing `Notification` model

---

## Task 1: Add `hackathon_created` Notification Type

**Files:**
- Modify: `synnovator/notifications/models.py:26-40`

**Step 1: Read the current notification_type choices**

Run: Read the file to confirm current choices list

**Step 2: Add new notification type**

Edit `synnovator/notifications/models.py`, find the `notification_type` field choices and add `hackathon_created`:

```python
    notification_type = models.CharField(
        max_length=50,
        choices=[
            ('violation_alert', _('Rule Violation Alert')),
            ('deadline_reminder', _('Deadline Reminder')),
            ('advancement_result', _('Advancement Result')),
            ('submission_reviewed', _('Submission Reviewed')),
            ('team_invitation', _('Team Invitation')),
            ('comment_reply', _('Comment Reply')),
            ('post_liked', _('Post Liked')),
            ('new_follower', _('New Follower')),
            ('system_announcement', _('System Announcement')),
            ('login_success', _('Login Success')),  # NEW
            ('hackathon_created', _('New Hackathon Created')),  # NEW
        ],
        verbose_name=_("Notification Type"),
        db_index=True
    )
```

**Step 3: Verify syntax**

Run: `uv run python -c "import django; django.setup(); from synnovator.notifications.models import Notification; print('OK')" 2>&1`

Expected: `OK`

**Step 4: Commit**

```bash
git add synnovator/notifications/models.py
git commit -m "feat(notifications): add login_success and hackathon_created notification types"
```

---

## Task 2: Create Signal Handlers Module

**Files:**
- Create: `synnovator/notifications/signals.py`

**Step 1: Create signals.py with login and hackathon notification handlers**

Write `synnovator/notifications/signals.py`:

```python
"""
Signal handlers for notification triggers.

Handles:
- user_logged_in: Creates login success notification
- page_published: Creates hackathon created notification for admins
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from wagtail.signals import page_published

User = get_user_model()


@receiver(user_logged_in)
def notify_on_login(sender, request, user, **kwargs):
    """
    Create a login success notification when user logs in.
    """
    from synnovator.notifications.models import Notification

    Notification.objects.create(
        recipient=user,
        notification_type='login_success',
        title=_("Login Successful"),
        message=_("You have successfully logged in."),
        is_read=True,  # Mark as read by default since user just logged in
    )


@receiver(page_published)
def notify_admins_on_hackathon_created(sender, instance, **kwargs):
    """
    Notify admin users when a new HackathonPage is published for the first time.

    Only triggers on first publish (when first_published_at was just set).
    """
    from synnovator.hackathons.models import HackathonPage
    from synnovator.notifications.models import Notification

    # Only handle HackathonPage
    if not isinstance(instance, HackathonPage):
        return

    # Check if this is the first publish by checking if first_published_at
    # was set in this save (it's a new value)
    revision = kwargs.get('revision')
    if revision is None:
        return

    # Get the page's previous revision to check if this is first publish
    # If first_published_at equals latest_revision_created_at, it's first publish
    if instance.first_published_at != instance.latest_revision_created_at:
        return  # Not first publish, skip

    # Get all superusers (admins) except the page owner
    admins = User.objects.filter(is_superuser=True)
    if instance.owner:
        admins = admins.exclude(id=instance.owner.id)

    creator_name = instance.owner.username if instance.owner else _("Someone")

    # Create notification for each admin
    for admin in admins:
        Notification.objects.create(
            recipient=admin,
            notification_type='hackathon_created',
            title=_("New Hackathon Created"),
            message=_("{username} created a new hackathon: {title}").format(
                username=creator_name,
                title=instance.title
            ),
            link_url=instance.get_url() or '',
            metadata={
                'hackathon_id': instance.id,
                'hackathon_title': instance.title,
                'created_by': instance.owner.username if instance.owner else None,
            },
            is_read=False,
        )
```

**Step 2: Verify syntax**

Run: `uv run python -c "import synnovator.notifications.signals; print('OK')"`

Expected: Error (signals not registered yet, but syntax OK)

**Step 3: Commit**

```bash
git add synnovator/notifications/signals.py
git commit -m "feat(notifications): add signal handlers for login and hackathon notifications"
```

---

## Task 3: Register Signals in Apps.py

**Files:**
- Modify: `synnovator/notifications/apps.py`

**Step 1: Update apps.py to register signals**

Edit `synnovator/notifications/apps.py`:

```python
from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'synnovator.notifications'

    def ready(self):
        # Import signals to register them
        import synnovator.notifications.signals  # noqa: F401
```

**Step 2: Verify signals are registered**

Run: `DJANGO_SETTINGS_MODULE=synnovator.settings.dev uv run python -c "import django; django.setup(); from django.contrib.auth.signals import user_logged_in; print('Receivers:', len(user_logged_in.receivers))"`

Expected: `Receivers: 1` (or more if other receivers exist)

**Step 3: Commit**

```bash
git add synnovator/notifications/apps.py
git commit -m "feat(notifications): register signal handlers in app ready"
```

---

## Task 4: Update Notification Template for New Types

**Files:**
- Modify: `templates/notifications/notification_list.html:27-45`

**Step 1: Add icons for new notification types**

Edit `templates/notifications/notification_list.html`, find the icon section and add cases for `login_success` and `hackathon_created`:

Replace the entire icon block (lines ~27-45) with:

```html
                        {# Notification Icon #}
                        <div class="flex-shrink-0">
                            {% if notification.notification_type == 'violation_alert' %}
                                <div class="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center">
                                    <svg class="w-5 h-5 text-red-600 dark:text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                        <path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495ZM10 5a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 10 5Zm0 9a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z" clip-rule="evenodd" />
                                    </svg>
                                </div>
                            {% elif notification.notification_type == 'team_invitation' %}
                                <div class="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center">
                                    <svg class="w-5 h-5 text-green-600 dark:text-green-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                        <path d="M10 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM6 8a2 2 0 1 1-4 0 2 2 0 0 1 4 0ZM1.49 15.326a.78.78 0 0 1-.358-.442 3 3 0 0 1 4.308-3.516 6.484 6.484 0 0 0-1.905 3.959c-.023.222-.014.442.025.654a4.97 4.97 0 0 1-2.07-.655ZM16.44 15.98a4.97 4.97 0 0 0 2.07-.654.78.78 0 0 0 .357-.442 3 3 0 0 0-4.308-3.517 6.484 6.484 0 0 1 1.907 3.96 2.32 2.32 0 0 1-.026.654ZM18 8a2 2 0 1 1-4 0 2 2 0 0 1 4 0ZM5.304 16.19a.844.844 0 0 1-.277-.71 5 5 0 0 1 9.947 0 .843.843 0 0 1-.277.71A6.975 6.975 0 0 1 10 18a6.974 6.974 0 0 1-4.696-1.81Z" />
                                    </svg>
                                </div>
                            {% elif notification.notification_type == 'login_success' %}
                                <div class="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center">
                                    <svg class="w-5 h-5 text-green-600 dark:text-green-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                        <path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 0 1 .143 1.052l-8 10.5a.75.75 0 0 1-1.127.075l-4.5-4.5a.75.75 0 0 1 1.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 0 1 1.05-.143Z" clip-rule="evenodd" />
                                    </svg>
                                </div>
                            {% elif notification.notification_type == 'hackathon_created' %}
                                <div class="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center">
                                    <svg class="w-5 h-5 text-purple-600 dark:text-purple-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                        <path fill-rule="evenodd" d="M4.606 12.97a.75.75 0 0 1-.134 1.051 2.494 2.494 0 0 0-.93 2.437 2.494 2.494 0 0 0 2.437-.93.75.75 0 1 1 1.186.918 3.995 3.995 0 0 1-4.482 1.332.75.75 0 0 1-.461-.461 3.994 3.994 0 0 1 1.332-4.482.75.75 0 0 1 1.052.134Z" clip-rule="evenodd" />
                                        <path fill-rule="evenodd" d="M5.752 12A13.07 13.07 0 0 0 8 14.248v4.002c0 .414.336.75.75.75a5 5 0 0 0 4.797-6.414 12.984 12.984 0 0 0 5.45-10.848.75.75 0 0 0-.735-.735 12.984 12.984 0 0 0-10.849 5.45A5 5 0 0 0 1 11.25c.001.414.337.75.751.75h4.002ZM13 9a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z" clip-rule="evenodd" />
                                    </svg>
                                </div>
                            {% else %}
                                <div class="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                                    <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                        <path fill-rule="evenodd" d="M10 2a6 6 0 0 0-6 6c0 1.887-.454 3.665-1.257 5.234a.75.75 0 0 0 .515 1.076 32.91 32.91 0 0 0 3.256.508 3.5 3.5 0 0 0 6.972 0 32.903 32.903 0 0 0 3.256-.508.75.75 0 0 0 .515-1.076A11.448 11.448 0 0 1 16 8a6 6 0 0 0-6-6Zm0 14.5a2 2 0 0 1-1.95-1.557 33.54 33.54 0 0 0 3.9 0A2 2 0 0 1 10 16.5Z" clip-rule="evenodd" />
                                    </svg>
                                </div>
                            {% endif %}
                        </div>
```

**Step 2: Commit**

```bash
git add templates/notifications/notification_list.html
git commit -m "feat(notifications): add icons for login and hackathon notification types"
```

---

## Task 5: Write Tests for Signal Handlers

**Files:**
- Create: `synnovator/notifications/tests/test_signals.py`

**Step 1: Write test file**

Write `synnovator/notifications/tests/test_signals.py`:

```python
"""
Tests for notification signal handlers.
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings
from wagtail.models import Page

from synnovator.notifications.models import Notification

User = get_user_model()


class LoginNotificationSignalTest(TestCase):
    """Tests for login notification signal."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_login_creates_notification(self):
        """Logging in should create a login_success notification."""
        # Clear any existing notifications
        Notification.objects.filter(recipient=self.user).delete()

        # Login triggers the signal
        self.client.login(username='testuser', password='testpass123')

        # Check notification was created
        notification = Notification.objects.filter(
            recipient=self.user,
            notification_type='login_success'
        ).first()

        assert notification is not None
        assert notification.is_read is True  # Should be marked as read
        assert 'Login' in notification.title or 'login' in notification.title.lower()


class HackathonCreatedNotificationTest(TestCase):
    """Tests for hackathon created notification signal."""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.regular_user = User.objects.create_user(
            username='creator',
            email='creator@example.com',
            password='creatorpass123'
        )
        # Get root page for creating test pages
        self.root_page = Page.objects.get(depth=1)

        # Create a HackathonIndexPage first (required parent)
        from synnovator.hackathons.models import HackathonIndexPage
        self.index_page = HackathonIndexPage(
            title='Hackathons',
            slug='hackathons'
        )
        self.root_page.add_child(instance=self.index_page)

    def test_publishing_hackathon_notifies_admins(self):
        """Publishing a new hackathon should notify admin users."""
        from synnovator.hackathons.models import HackathonPage

        # Clear existing notifications
        Notification.objects.filter(recipient=self.admin_user).delete()

        # Create and publish a hackathon page
        hackathon = HackathonPage(
            title='Test Hackathon',
            slug='test-hackathon',
            owner=self.regular_user,
        )
        self.index_page.add_child(instance=hackathon)

        # Publish the page (this triggers the signal)
        revision = hackathon.save_revision()
        revision.publish()

        # Check notification was created for admin
        notification = Notification.objects.filter(
            recipient=self.admin_user,
            notification_type='hackathon_created'
        ).first()

        assert notification is not None
        assert notification.is_read is False
        assert 'creator' in notification.message
        assert 'Test Hackathon' in notification.message

    def test_creator_not_notified_of_own_hackathon(self):
        """The hackathon creator should not receive notification."""
        from synnovator.hackathons.models import HackathonPage

        # Make regular_user a superuser too
        self.regular_user.is_superuser = True
        self.regular_user.save()

        # Clear existing notifications
        Notification.objects.filter(recipient=self.regular_user).delete()

        # Create and publish hackathon as regular_user
        hackathon = HackathonPage(
            title='My Hackathon',
            slug='my-hackathon',
            owner=self.regular_user,
        )
        self.index_page.add_child(instance=hackathon)
        revision = hackathon.save_revision()
        revision.publish()

        # Creator should NOT receive notification even if they're an admin
        notification = Notification.objects.filter(
            recipient=self.regular_user,
            notification_type='hackathon_created'
        ).first()

        assert notification is None
```

**Step 2: Run tests to verify they fail initially (TDD)**

Run: `uv run python manage.py test synnovator.notifications.tests.test_signals -v 2`

Expected: Tests should pass if signals are correctly wired

**Step 3: Commit**

```bash
git add synnovator/notifications/tests/test_signals.py
git commit -m "test(notifications): add tests for login and hackathon notification signals"
```

---

## Task 6: Create Management Command to Seed Admin Login Notification

**Files:**
- Create: `synnovator/notifications/management/__init__.py`
- Create: `synnovator/notifications/management/commands/__init__.py`
- Create: `synnovator/notifications/management/commands/seed_admin_notification.py`

**Step 1: Create directory structure**

```bash
mkdir -p synnovator/notifications/management/commands
touch synnovator/notifications/management/__init__.py
touch synnovator/notifications/management/commands/__init__.py
```

**Step 2: Create seed command**

Write `synnovator/notifications/management/commands/seed_admin_notification.py`:

```python
"""
Management command to seed initial notification for admin user.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from synnovator.notifications.models import Notification

User = get_user_model()


class Command(BaseCommand):
    help = 'Create initial login success notification for admin user'

    def handle(self, *args, **options):
        try:
            admin = User.objects.get(username='admin')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Admin user not found. Create one first.')
            )
            return

        # Check if login notification already exists
        existing = Notification.objects.filter(
            recipient=admin,
            notification_type='login_success'
        ).exists()

        if existing:
            self.stdout.write(
                self.style.WARNING('Login notification already exists for admin.')
            )
            return

        Notification.objects.create(
            recipient=admin,
            notification_type='login_success',
            title='Login Successful',
            message='You have successfully logged in.',
            is_read=True,
        )

        self.stdout.write(
            self.style.SUCCESS('Created login success notification for admin.')
        )
```

**Step 3: Run the command**

Run: `uv run python manage.py seed_admin_notification`

Expected: `Created login success notification for admin.`

**Step 4: Commit**

```bash
git add synnovator/notifications/management/
git commit -m "feat(notifications): add management command to seed admin notification"
```

---

## Task 7: End-to-End Verification

**Step 1: Restart the development server**

Run: `uv run python manage.py runserver` (in a separate terminal)

**Step 2: Verify admin can see login notification**

1. Open browser to http://127.0.0.1:8000/en/admin/
2. Login as `admin` / `password`
3. Navigate to http://127.0.0.1:8000/en/notifications/
4. Verify: Should see "Login Successful" notification (marked as read)

**Step 3: Create test user for hackathon creation**

Run: `uv run python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_user('testcreator', 'test@example.com', 'password')"`

**Step 4: Create hackathon as different user**

1. Logout from admin
2. Login as `testcreator` / `password`
3. Go to http://127.0.0.1:8000/admin/pages/
4. Navigate to Hackathons index page
5. Click "Add child page" > "Hackathon Page"
6. Fill in title: "Test Hackathon by Creator"
7. Click "Publish"

**Step 5: Verify admin receives notification**

1. Logout from testcreator
2. Login as `admin` / `password`
3. Navigate to http://127.0.0.1:8000/en/notifications/
4. Verify: Should see UNREAD "testcreator created a new hackathon: Test Hackathon by Creator"

**Step 6: Final commit**

```bash
git add -A
git commit -m "feat(notifications): complete notification trigger system implementation"
```

---

## Summary

| Component | File | Purpose |
|-----------|------|---------|
| Model update | `synnovator/notifications/models.py` | Add new notification types |
| Signal handlers | `synnovator/notifications/signals.py` | Login + hackathon publish triggers |
| App config | `synnovator/notifications/apps.py` | Register signals on startup |
| Template | `templates/notifications/notification_list.html` | Icons for new types |
| Tests | `synnovator/notifications/tests/test_signals.py` | Verify signal behavior |
| Seed command | `synnovator/notifications/management/commands/seed_admin_notification.py` | Initial data |

**Acceptance Criteria:**
1. ✅ Admin sees "Login Successful" (read) at http://127.0.0.1:8000/en/notifications/
2. ✅ When another user publishes a hackathon, admin sees unread notification
