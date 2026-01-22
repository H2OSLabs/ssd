"""
Root pytest configuration for Synnovator.

This file provides shared fixtures for all tests in the project.
App-specific fixtures should be defined in each app's tests/conftest.py.
"""

import pytest
from django.contrib.auth import get_user_model
from wagtail.models import Page, Site

User = get_user_model()


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Ensure database is ready for tests."""
    pass


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    user = User.objects.create_superuser(
        username="admin",
        email="admin@test.com",
        password="password123",
    )
    return user


@pytest.fixture
def regular_user(db):
    """Create a regular user."""
    user = User.objects.create_user(
        username="user",
        email="user@test.com",
        password="password123",
    )
    return user


@pytest.fixture
def wagtail_root(db):
    """Get or create Wagtail root page."""
    root = Page.objects.filter(depth=1).first()
    if not root:
        root = Page.add_root(title="Root", slug="root")
    return root


@pytest.fixture
def default_site(db, wagtail_root):
    """Ensure default site exists."""
    # Try to get existing home page or create one
    from synnovator.home.models import HomePage

    home = HomePage.objects.first()
    if not home:
        home = HomePage(title="Home", slug="home")
        wagtail_root.add_child(instance=home)

    site, _ = Site.objects.get_or_create(
        is_default_site=True,
        defaults={
            "hostname": "localhost",
            "root_page": home,
            "site_name": "Test Site",
        },
    )
    return site


@pytest.fixture
def authenticated_client(client, regular_user):
    """Return a client with a logged-in regular user."""
    client.force_login(regular_user)
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Return a client with a logged-in admin user."""
    client.force_login(admin_user)
    return client
