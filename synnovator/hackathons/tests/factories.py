"""
Factory Boy factories for hackathons app.
"""

import factory
from factory.django import DjangoModelFactory
from django.utils import timezone
from datetime import timedelta
from wagtail.models import Page

from synnovator.hackathons.models import (
    HackathonIndexPage,
    HackathonPage,
    Phase,
    Prize,
    Quest,
    QuestIndexPage,
    Team,
    TeamMember,
    Submission,
    SubmissionIndexPage,
    SubmissionPage,
)
from synnovator.users.tests.factories import UserFactory
from synnovator.community.models import TeamProfilePage


class HackathonIndexPageFactory(DjangoModelFactory):
    """Factory for HackathonIndexPage."""

    class Meta:
        model = HackathonIndexPage

    title = "Hackathons"
    slug = factory.Sequence(lambda n: f"hackathons-{n}")
    introduction = "Welcome to our hackathons!"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override to handle Wagtail page tree structure."""
        parent = kwargs.pop("parent", None)
        if parent is None:
            parent = Page.objects.filter(depth=1).first()
            if not parent:
                parent = Page.add_root(title="Root", slug="root")

        instance = model_class(*args, **kwargs)
        parent.add_child(instance=instance)
        return HackathonIndexPage.objects.get(pk=instance.pk)


class QuestIndexPageFactory(DjangoModelFactory):
    """Factory for QuestIndexPage."""

    class Meta:
        model = QuestIndexPage

    title = "Quests"
    slug = factory.Sequence(lambda n: f"quests-{n}")
    introduction = "Welcome to our quests!"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override to handle Wagtail page tree structure."""
        parent = kwargs.pop("parent", None)
        if parent is None:
            parent = Page.objects.filter(depth=1).first()
            if not parent:
                parent = Page.add_root(title="Root", slug="root")

        instance = model_class(*args, **kwargs)
        parent.add_child(instance=instance)
        return QuestIndexPage.objects.get(pk=instance.pk)


class HackathonPageFactory(DjangoModelFactory):
    """Factory for HackathonPage."""

    class Meta:
        model = HackathonPage

    title = factory.Sequence(lambda n: f"Hackathon {n}")
    slug = factory.Sequence(lambda n: f"hackathon-{n}")
    description = factory.Faker("paragraph")
    status = "upcoming"
    min_team_size = 2
    max_team_size = 5
    allow_solo = False
    required_roles = factory.LazyFunction(lambda: [])
    passing_score = 80.0

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override to handle Wagtail page tree structure."""
        parent = kwargs.pop("parent", None)
        if parent is None:
            # Find or create HackathonIndexPage as parent
            index = HackathonIndexPage.objects.first()
            if not index:
                root = Page.objects.filter(depth=1).first()
                if not root:
                    root = Page.add_root(title="Root", slug="root")
                index = HackathonIndexPageFactory(parent=root)
            parent = index

        instance = model_class(*args, **kwargs)
        parent.add_child(instance=instance)
        return HackathonPage.objects.get(pk=instance.pk)


class QuestFactory(DjangoModelFactory):
    """Factory for Quest snippet."""

    class Meta:
        model = Quest

    title = factory.Sequence(lambda n: f"Quest {n}")
    slug = factory.Sequence(lambda n: f"quest-{n}")
    description = factory.Faker("paragraph")
    quest_type = "technical"
    difficulty = "intermediate"
    xp_reward = factory.Faker("random_int", min=10, max=100)
    estimated_time_minutes = 60
    is_active = True
    tags = factory.LazyFunction(lambda: ["python", "api"])


class TechnicalQuestFactory(QuestFactory):
    """Factory for technical quests."""

    quest_type = "technical"
    tags = factory.LazyFunction(lambda: ["python", "machine-learning", "api"])


class CommercialQuestFactory(QuestFactory):
    """Factory for commercial quests."""

    quest_type = "commercial"
    tags = factory.LazyFunction(lambda: ["business", "marketing", "pitch"])


class OperationalQuestFactory(QuestFactory):
    """Factory for operational quests."""

    quest_type = "operational"
    tags = factory.LazyFunction(lambda: ["design", "ux", "user-research"])


class PhaseFactory(DjangoModelFactory):
    """Factory for Phase inline model."""

    class Meta:
        model = Phase

    hackathon = factory.SubFactory(HackathonPageFactory)
    title = factory.Sequence(lambda n: f"Phase {n}")
    description = factory.Faker("paragraph")
    start_date = factory.LazyFunction(lambda: timezone.now())
    end_date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))
    order = factory.Sequence(lambda n: n)
    requirements = factory.LazyFunction(lambda: {})


class ActivePhaseFactory(PhaseFactory):
    """Factory for currently active phases."""

    start_date = factory.LazyFunction(lambda: timezone.now() - timedelta(days=1))
    end_date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=6))


class FuturePhaseFactory(PhaseFactory):
    """Factory for future phases."""

    start_date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))
    end_date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=14))


class PastPhaseFactory(PhaseFactory):
    """Factory for past phases."""

    start_date = factory.LazyFunction(lambda: timezone.now() - timedelta(days=14))
    end_date = factory.LazyFunction(lambda: timezone.now() - timedelta(days=7))


class PrizeFactory(DjangoModelFactory):
    """Factory for Prize inline model."""

    class Meta:
        model = Prize

    hackathon = factory.SubFactory(HackathonPageFactory)
    title = factory.Sequence(lambda n: f"Prize {n}")
    description = factory.Faker("sentence")
    rank = factory.Sequence(lambda n: n + 1)
    monetary_value = factory.Faker("random_int", min=100, max=10000)
    benefits = factory.LazyFunction(lambda: [])


class TeamFactory(DjangoModelFactory):
    """Factory for Team."""

    class Meta:
        model = Team

    hackathon = factory.SubFactory(HackathonPageFactory)
    name = factory.Sequence(lambda n: f"Team {n}")
    slug = factory.Sequence(lambda n: f"team-{n}")
    tagline = factory.Faker("sentence")
    status = "forming"
    is_seeking_members = True
    final_score = 0.0
    technical_score = 0.0
    commercial_score = 0.0
    operational_score = 0.0


class ActiveTeamFactory(TeamFactory):
    """Factory for teams that are ready for competition."""

    status = "ready"
    is_seeking_members = False


class ScoredTeamFactory(TeamFactory):
    """Factory for teams with scores."""

    status = "verified"
    is_seeking_members = False
    final_score = factory.Faker("pydecimal", left_digits=2, right_digits=2, min_value=50, max_value=100)
    technical_score = factory.Faker("pydecimal", left_digits=2, right_digits=2, min_value=50, max_value=100)
    commercial_score = factory.Faker("pydecimal", left_digits=2, right_digits=2, min_value=50, max_value=100)
    operational_score = factory.Faker("pydecimal", left_digits=2, right_digits=2, min_value=50, max_value=100)


class TeamMemberFactory(DjangoModelFactory):
    """Factory for TeamMember through model."""

    class Meta:
        model = TeamMember

    team = factory.SubFactory(TeamFactory)
    user = factory.SubFactory(UserFactory)
    role = "hacker"
    is_leader = False


class LeaderTeamMemberFactory(TeamMemberFactory):
    """Factory for team leaders."""

    is_leader = True


class SubmissionFactory(DjangoModelFactory):
    """Factory for Submission."""

    class Meta:
        model = Submission

    user = factory.SubFactory(UserFactory)
    quest = factory.SubFactory(QuestFactory)
    team = None
    hackathon = None
    submission_url = factory.Faker("url")
    description = factory.Faker("paragraph")
    verification_status = "pending"
    copyright_declaration = True
    file_transfer_confirmed = True


class TeamSubmissionFactory(DjangoModelFactory):
    """Factory for team hackathon submissions."""

    class Meta:
        model = Submission

    user = None
    quest = None
    team = factory.SubFactory(TeamFactory)
    hackathon = factory.LazyAttribute(lambda o: o.team.hackathon)
    submission_url = factory.Faker("url")
    description = factory.Faker("paragraph")
    verification_status = "pending"
    copyright_declaration = True
    file_transfer_confirmed = True


class VerifiedSubmissionFactory(SubmissionFactory):
    """Factory for verified submissions."""

    verification_status = "verified"
    score = factory.Faker("pydecimal", left_digits=2, right_digits=2, min_value=60, max_value=100)
    verified_at = factory.LazyFunction(timezone.now)
    verified_by = factory.SubFactory(UserFactory)


class SubmissionIndexPageFactory(DjangoModelFactory):
    """Factory for SubmissionIndexPage."""

    class Meta:
        model = SubmissionIndexPage

    title = "Submissions"
    slug = factory.Sequence(lambda n: f"submissions-{n}")
    intro = "Browse all submissions"
    enable_hackathon_filter = True
    enable_date_filter = True
    enable_submitter_filter = True
    enable_team_filter = True
    enable_status_filter = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override to handle Wagtail page tree structure."""
        parent = kwargs.pop("parent", None)
        if parent is None:
            parent = Page.objects.filter(depth=1).first()
            if not parent:
                parent = Page.add_root(title="Root", slug="root")

        instance = model_class(*args, **kwargs)
        parent.add_child(instance=instance)
        return SubmissionIndexPage.objects.get(pk=instance.pk)


class SubmissionPageFactory(DjangoModelFactory):
    """Factory for SubmissionPage."""

    class Meta:
        model = SubmissionPage

    title = factory.Sequence(lambda n: f"Project Submission {n}")
    slug = factory.Sequence(lambda n: f"submission-{n}")
    tagline = factory.Faker("sentence")
    verification_status = "draft"
    submitter = factory.SubFactory(UserFactory)
    team_profile = None

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override to handle Wagtail page tree structure."""
        parent = kwargs.pop("parent", None)
        hackathons = kwargs.pop("hackathons", [])

        if parent is None:
            # Find or create SubmissionIndexPage as parent
            index = SubmissionIndexPage.objects.first()
            if not index:
                root = Page.objects.filter(depth=1).first()
                if not root:
                    root = Page.add_root(title="Root", slug="root")
                index = SubmissionIndexPageFactory(parent=root)
            parent = index

        instance = model_class(*args, **kwargs)
        parent.add_child(instance=instance)

        # Refresh to get the saved instance
        instance = SubmissionPage.objects.get(pk=instance.pk)

        # Add hackathons M2M relationship
        if hackathons:
            instance.hackathons.set(hackathons)

        return instance


class TeamSubmissionPageFactory(SubmissionPageFactory):
    """Factory for team SubmissionPage."""

    submitter = None

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # Need to handle team_profile creation separately since it's a Wagtail page
        team_profile = kwargs.pop("team_profile", None)

        instance = super()._create(model_class, *args, **kwargs)

        if team_profile:
            instance.team_profile = team_profile
            instance.save()

        return instance
