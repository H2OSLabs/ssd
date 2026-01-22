"""
Factory Boy factories for community app.
"""

import factory
from factory.django import DjangoModelFactory

from synnovator.community.models import (
    CommunityPost,
    Comment,
    Like,
    UserFollow,
    Report,
    TeamIndexPage,
    TeamProfilePage,
    TeamMembership,
)
from synnovator.users.tests.factories import UserFactory
from synnovator.hackathons.tests.factories import HackathonPageFactory
from wagtail.models import Page


class CommunityPostFactory(DjangoModelFactory):
    """Factory for CommunityPost snippet."""

    class Meta:
        model = CommunityPost

    author = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Post {n}")
    content = factory.Faker("paragraph")
    status = "published"
    hackathon = None


class DraftPostFactory(CommunityPostFactory):
    """Factory for draft posts."""

    status = "draft"


class FlaggedPostFactory(CommunityPostFactory):
    """Factory for flagged posts."""

    status = "flagged"
    moderation_notes = "Flagged for review"


class HackathonPostFactory(CommunityPostFactory):
    """Factory for posts linked to hackathon."""

    hackathon = factory.SubFactory(HackathonPageFactory)


class CommentFactory(DjangoModelFactory):
    """Factory for Comment."""

    class Meta:
        model = Comment

    post = factory.SubFactory(CommunityPostFactory)
    author = factory.SubFactory(UserFactory)
    content = factory.Faker("sentence")
    status = "visible"
    parent = None


class ReplyCommentFactory(CommentFactory):
    """Factory for comment replies."""

    parent = factory.SubFactory(CommentFactory)


class PostLikeFactory(DjangoModelFactory):
    """Factory for post likes."""

    class Meta:
        model = Like

    user = factory.SubFactory(UserFactory)
    post = factory.SubFactory(CommunityPostFactory)
    comment = None


class CommentLikeFactory(DjangoModelFactory):
    """Factory for comment likes."""

    class Meta:
        model = Like

    user = factory.SubFactory(UserFactory)
    post = None
    comment = factory.SubFactory(CommentFactory)


class UserFollowFactory(DjangoModelFactory):
    """Factory for UserFollow."""

    class Meta:
        model = UserFollow

    follower = factory.SubFactory(UserFactory)
    following = factory.SubFactory(UserFactory)


class PostReportFactory(DjangoModelFactory):
    """Factory for post reports."""

    class Meta:
        model = Report

    reporter = factory.SubFactory(UserFactory)
    post = factory.SubFactory(CommunityPostFactory)
    comment = None
    reason = "spam"
    status = "pending"


class CommentReportFactory(DjangoModelFactory):
    """Factory for comment reports."""

    class Meta:
        model = Report

    reporter = factory.SubFactory(UserFactory)
    post = None
    comment = factory.SubFactory(CommentFactory)
    reason = "harassment"
    status = "pending"


# =============================================================================
# Team Management Factories
# =============================================================================


class TeamIndexPageFactory(DjangoModelFactory):
    """Factory for TeamIndexPage."""

    class Meta:
        model = TeamIndexPage

    title = "Teams"
    slug = "teams"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Create the page under the root page."""
        obj = model_class(*args, **kwargs)
        root = Page.objects.filter(depth=1).first()
        if root:
            root.add_child(instance=obj)
        return obj


class TeamProfilePageFactory(DjangoModelFactory):
    """Factory for TeamProfilePage."""

    class Meta:
        model = TeamProfilePage

    title = factory.Sequence(lambda n: f"Team {n}")
    slug = factory.LazyAttribute(lambda o: o.title.lower().replace(' ', '-'))
    tagline = factory.Faker("sentence")
    is_open_for_members = True
    max_members = 10

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Create the team page under a TeamIndexPage."""
        # Get or create team index
        team_index = TeamIndexPage.objects.first()
        if not team_index:
            team_index = TeamIndexPageFactory()

        obj = model_class(*args, **kwargs)
        team_index.add_child(instance=obj)
        return obj


class TeamMembershipFactory(DjangoModelFactory):
    """Factory for TeamMembership."""

    class Meta:
        model = TeamMembership

    team = factory.SubFactory(TeamProfilePageFactory)
    user = factory.SubFactory(UserFactory)
    role = "member"
    is_leader = False
