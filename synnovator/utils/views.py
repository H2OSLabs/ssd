"""Test views for layout components."""
from datetime import datetime, timedelta
from django.views.generic import TemplateView
from django.utils import timezone


class ThreePaneLayoutTestView(TemplateView):
    """Test view for three-pane layout."""

    template_name = "layouts/three_pane_test.html"


class ComponentTestView(TemplateView):
    """Test view for displaying all four components with sample data."""

    template_name = "pages/component_test_page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Sample breadcrumbs
        context['sample_breadcrumbs'] = [
            {'name': 'Home', 'url': '/'},
            {'name': 'Hackathons', 'url': '/hackathons/'},
            {'name': 'AI Innovation Challenge 2026', 'url': '/hackathons/ai-challenge-2026/'},
            {'name': 'Submissions', 'url': '#'},
        ]

        # Sample quests - using a simple class to make templates work
        class MockQuest:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)

            def get_difficulty_display(self):
                return self.difficulty.capitalize() if self.difficulty else None

        context['sample_quests'] = [
            MockQuest(
                title='Build a REST API with Django',
                url='#',
                difficulty='easy',
                xp_reward=150,
                estimated_hours=3,
                skills=['Python', 'Django', 'REST API', 'PostgreSQL', 'Testing'],
                progress=None,
            ),
            MockQuest(
                title='Implement Real-time Chat with WebSockets',
                url='#',
                difficulty='hard',
                xp_reward=500,
                estimated_hours=8,
                skills=['WebSockets', 'Redis', 'Django Channels', 'JavaScript', 'Real-time'],
                progress=65,
            ),
        ]

        # Sample users - using a simple class to make templates work
        class MockUser:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)

            def get_full_name(self):
                return f"{self.first_name} {self.last_name}"

            def get_role_display(self):
                return self.role.capitalize()

        context['sample_users'] = [
            MockUser(
                username='alice_dev',
                first_name='Alice',
                last_name='Johnson',
                avatar=None,
                level=12,
                role='hacker',
                skills=['Python', 'Django', 'React', 'PostgreSQL', 'Docker', 'AWS'],
                xp=3450,
                reputation=892,
                seeking_team=True,
                profile_url='#',
            ),
            MockUser(
                username='bob_designer',
                first_name='Bob',
                last_name='Smith',
                avatar=None,
                level=8,
                role='hipster',
                skills=['UI/UX', 'Figma', 'Adobe XD', 'Tailwind CSS', 'Design Systems'],
                xp=1820,
                reputation=456,
                seeking_team=False,
                profile_url='#',
            ),
            MockUser(
                username='charlie_biz',
                first_name='Charlie',
                last_name='Brown',
                avatar=None,
                level=15,
                role='hustler',
                skills=['Product Management', 'Marketing', 'Business Strategy', 'Analytics'],
                xp=5230,
                reputation=1234,
                seeking_team=True,
                profile_url='#',
            ),
        ]

        # Sample submissions - using a simple class to make templates work
        class MockSubmission:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)

            def get_status_display(self):
                return self.status.capitalize()

        now = timezone.now()
        context['sample_submissions'] = [
            MockSubmission(
                status='verified',
                score=95,
                repo_url='https://github.com/alice/awesome-project',
                created_at=now - timedelta(hours=2),
                feedback='Excellent work! Your implementation demonstrates strong understanding of Django best practices. The test coverage is comprehensive and the code is well-documented.',
            ),
            MockSubmission(
                status='failed',
                score=None,
                repo_url='https://github.com/bob/prototype-app',
                created_at=now - timedelta(days=1),
                feedback='The submission did not pass all verification tests. Please review the following:\n\n1. Missing test cases for authentication endpoints\n2. Database migrations not included\n3. Environment variables not documented in README',
            ),
            MockSubmission(
                status='verifying',
                score=None,
                repo_url='https://github.com/charlie/innovation-platform',
                created_at=now - timedelta(minutes=15),
                feedback=None,
            ),
        ]

        return context
