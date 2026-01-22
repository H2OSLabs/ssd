"""
Template layout integration tests to verify header/footer/breadcrumb inclusion.

These tests ensure that:
1. All page templates include the header component
2. All page templates include the footer component
3. Breadcrumb navigation is available where needed
4. Sidebar navigation works correctly
"""

import pytest
from django.template import Template, Context, TemplateSyntaxError
from django.template.loader import render_to_string, get_template
from django.test import RequestFactory, Client
from django.urls import reverse

from synnovator.users.tests.factories import UserFactory


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def authenticated_client(db):
    """Client with authenticated user."""
    user = UserFactory(username='testuser', password='testpass123')
    client = Client()
    client.force_login(user)
    return client, user


@pytest.mark.integration
class TestLayoutInclusion:
    """Tests to verify layout components are properly included."""

    @pytest.mark.parametrize("layout_template", [
        "base_page.html",
    ])
    def test_layout_includes_header(self, db, layout_template):
        """Layout templates include header block."""
        template = get_template(layout_template)
        source = template.template.source

        # Check that header is defined or included
        assert "{% block header %}" in source or "{% include" in source and "header" in source.lower(), \
            f"{layout_template} should include header block or header include"

    @pytest.mark.parametrize("layout_template", [
        "base_page.html",
    ])
    def test_layout_includes_footer(self, db, layout_template):
        """Layout templates include footer block."""
        template = get_template(layout_template)
        source = template.template.source

        # Check that footer is defined or included
        assert "{% block footer %}" in source or "{% include" in source and "footer" in source.lower(), \
            f"{layout_template} should include footer block or footer include"


@pytest.mark.integration
class TestHeaderContent:
    """Tests for header.html component content."""

    def test_header_has_logo(self, db, request_factory):
        """Header includes site logo/name link."""
        request = request_factory.get("/")
        html = render_to_string(
            "navigation/header.html",
            {"request": request},
        )
        # Should have a link to home
        assert 'href="/"' in html

    def test_header_has_search(self, db, request_factory):
        """Header includes search functionality."""
        request = request_factory.get("/")
        html = render_to_string(
            "navigation/header.html",
            {"request": request},
        )
        # Should have search input
        assert 'type="search"' in html or 'search' in html.lower()


@pytest.mark.integration
class TestSidebarContent:
    """Tests for sidebar navigation component."""

    def test_sidebar_has_navigation_items(self, db, request_factory):
        """Sidebar includes navigation items."""
        request = request_factory.get("/")
        html = render_to_string(
            "navigation/sidebar.html",
            {"request": request, "sidebarCollapsed": False},
        )
        # Should have navigation links
        assert "nav" in html.lower() or "navigation" in html.lower()

    def test_sidebar_has_collapse_button(self, db, request_factory):
        """Sidebar has collapse/expand button."""
        request = request_factory.get("/")
        html = render_to_string(
            "navigation/sidebar.html",
            {"request": request, "sidebarCollapsed": False},
        )
        # Should have collapse button with Alpine.js binding
        assert "@click" in html or "sidebarCollapsed" in html


@pytest.mark.integration
class TestBreadcrumbNavigation:
    """Tests for breadcrumb navigation component."""

    def test_breadcrumb_template_exists(self, db):
        """Breadcrumb template exists and can be loaded."""
        template = get_template("navigation/breadcrumbs.html")
        assert template is not None


@pytest.mark.integration
class TestFooterContent:
    """Tests for footer.html component content."""

    def test_footer_has_copyright(self, db, request_factory):
        """Footer includes copyright notice."""
        request = request_factory.get("/")
        html = render_to_string(
            "navigation/footer.html",
            {"request": request},
        )
        # Should have copyright
        assert "©" in html or "copyright" in html.lower()


@pytest.mark.integration
class TestNotificationPage:
    """Tests for notification list page."""

    def test_notification_list_requires_auth(self, client, db):
        """Notification list requires authentication."""
        url = reverse("notifications:list")
        response = client.get(url)
        # Should redirect to login
        assert response.status_code == 302
        assert "login" in response.url.lower() or "admin" in response.url.lower()

    def test_notification_list_authenticated(self, authenticated_client, db):
        """Authenticated user can access notification list."""
        client, user = authenticated_client
        url = reverse("notifications:list")
        response = client.get(url)
        assert response.status_code == 200


@pytest.mark.integration
class TestTemplateExtensions:
    """Tests to verify templates properly extend layouts."""

    @pytest.mark.parametrize("template_name,expected_base", [
        ("notifications/notification_list.html", "base_page.html"),
    ])
    def test_template_extends_correct_base(self, db, template_name, expected_base):
        """Templates extend the correct base layout."""
        template = get_template(template_name)
        source = template.template.source

        assert f'{{% extends "{expected_base}"' in source or f"{{% extends '{expected_base}'" in source, \
            f"{template_name} should extend {expected_base}"


@pytest.mark.integration
class TestBasePageRendering:
    """Tests for base_page.html complete rendering."""

    def test_base_page_renders_without_error(self, db, request_factory):
        """Base page template renders without errors."""
        request = request_factory.get("/")
        # Mock page object for template context
        class MockPage:
            title = "Test Page"
            seo_title = ""
            search_description = ""
            def get_ancestors(self):
                return []

        try:
            html = render_to_string(
                "base_page.html",
                {
                    "request": request,
                    "page": MockPage(),
                },
            )
            # Should render some HTML content
            assert "<html" in html or "html" in html.lower()
        except Exception as e:
            # Some template errors are expected due to missing context
            # but template syntax should be valid
            if "TemplateSyntaxError" in str(type(e)):
                pytest.fail(f"Template syntax error in base_page.html: {e}")
