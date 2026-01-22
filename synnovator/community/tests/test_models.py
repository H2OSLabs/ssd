"""
Tests for community models.
"""

import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from synnovator.community.tests.factories import (
    CommunityPostFactory,
    DraftPostFactory,
    FlaggedPostFactory,
    HackathonPostFactory,
    CommentFactory,
    ReplyCommentFactory,
    PostLikeFactory,
    CommentLikeFactory,
    UserFollowFactory,
    PostReportFactory,
    CommentReportFactory,
    TeamIndexPageFactory,
    TeamProfilePageFactory,
    TeamMembershipFactory,
)
from synnovator.users.tests.factories import UserFactory


class TestCommunityPost:
    """Tests for CommunityPost snippet model."""

    def test_post_creation(self, db):
        """CommunityPost can be created."""
        post = CommunityPostFactory()
        assert post.pk is not None
        assert post.author is not None
        assert post.title

    def test_post_str_representation(self, db):
        """CommunityPost __str__ returns title and author."""
        author = UserFactory(username="testauthor")
        post = CommunityPostFactory(author=author, title="Test Post")
        assert str(post) == "Test Post by testauthor"

    def test_post_default_status(self, db):
        """Post default status is published from factory."""
        post = CommunityPostFactory()
        assert post.status == "published"

    def test_post_status_choices(self, db):
        """Post accepts valid status choices."""
        statuses = ["draft", "published", "flagged", "removed"]
        for status in statuses:
            post = CommunityPostFactory(status=status)
            assert post.status == status

    def test_draft_post(self, db):
        """Draft post can be created."""
        post = DraftPostFactory()
        assert post.status == "draft"

    def test_flagged_post(self, db):
        """Flagged post has moderation notes."""
        post = FlaggedPostFactory()
        assert post.status == "flagged"
        assert post.moderation_notes

    def test_post_linked_to_hackathon(self, db):
        """Post can be linked to hackathon."""
        post = HackathonPostFactory()
        assert post.hackathon is not None

    def test_post_get_like_count_zero(self, db):
        """get_like_count returns 0 when no likes."""
        post = CommunityPostFactory()
        assert post.get_like_count() == 0

    def test_post_get_like_count(self, db):
        """get_like_count returns correct count."""
        post = CommunityPostFactory()
        PostLikeFactory(post=post)
        PostLikeFactory(post=post)
        PostLikeFactory(post=post)
        assert post.get_like_count() == 3

    def test_post_get_comment_count_zero(self, db):
        """get_comment_count returns 0 when no comments."""
        post = CommunityPostFactory()
        assert post.get_comment_count() == 0

    def test_post_get_comment_count(self, db):
        """get_comment_count returns correct count."""
        post = CommunityPostFactory()
        CommentFactory(post=post)
        CommentFactory(post=post)
        assert post.get_comment_count() == 2


class TestComment:
    """Tests for Comment model."""

    def test_comment_creation(self, db):
        """Comment can be created."""
        comment = CommentFactory()
        assert comment.pk is not None
        assert comment.post is not None
        assert comment.author is not None

    def test_comment_str_representation(self, db):
        """Comment __str__ returns author and post."""
        author = UserFactory(username="commenter")
        post = CommunityPostFactory(title="Test Post")
        comment = CommentFactory(author=author, post=post)
        assert "commenter" in str(comment)
        assert "Test Post" in str(comment)

    def test_comment_default_status(self, db):
        """Comment default status is visible."""
        comment = CommentFactory()
        assert comment.status == "visible"

    def test_comment_status_choices(self, db):
        """Comment accepts valid status choices."""
        statuses = ["visible", "hidden", "flagged"]
        for status in statuses:
            comment = CommentFactory(status=status)
            assert comment.status == status

    def test_nested_comment_reply(self, db):
        """Comment can be reply to another comment."""
        parent = CommentFactory()
        reply = ReplyCommentFactory(parent=parent, post=parent.post)

        assert reply.parent == parent
        assert parent.replies.first() == reply

    def test_comment_get_like_count(self, db):
        """get_like_count returns correct count for comment."""
        comment = CommentFactory()
        CommentLikeFactory(comment=comment)
        CommentLikeFactory(comment=comment)
        assert comment.get_like_count() == 2


class TestLike:
    """Tests for Like model."""

    def test_post_like_creation(self, db):
        """Post like can be created."""
        like = PostLikeFactory()
        assert like.pk is not None
        assert like.post is not None
        assert like.comment is None

    def test_comment_like_creation(self, db):
        """Comment like can be created."""
        like = CommentLikeFactory()
        assert like.pk is not None
        assert like.comment is not None
        assert like.post is None

    def test_post_like_str_representation(self, db):
        """Post like __str__ shows user and post."""
        user = UserFactory(username="liker")
        post = CommunityPostFactory(title="Liked Post")
        like = PostLikeFactory(user=user, post=post)
        assert "liker" in str(like)
        assert "Liked Post" in str(like)

    def test_comment_like_str_representation(self, db):
        """Comment like __str__ shows user and comment author."""
        user = UserFactory(username="liker")
        comment_author = UserFactory(username="commenter")
        comment = CommentFactory(author=comment_author)
        like = CommentLikeFactory(user=user, comment=comment)
        assert "liker" in str(like)
        assert "commenter" in str(like)

    def test_like_requires_post_or_comment(self, db):
        """Like must have either post or comment."""
        from synnovator.community.models import Like

        user = UserFactory()
        like = Like(user=user, post=None, comment=None)

        with pytest.raises(ValidationError):
            like.clean()

    def test_like_cannot_have_both(self, db):
        """Like cannot have both post and comment."""
        from synnovator.community.models import Like

        user = UserFactory()
        post = CommunityPostFactory()
        comment = CommentFactory()
        like = Like(user=user, post=post, comment=comment)

        with pytest.raises(ValidationError):
            like.clean()

    def test_user_cannot_like_post_twice(self, db):
        """User cannot like same post twice."""
        user = UserFactory()
        post = CommunityPostFactory()
        PostLikeFactory(user=user, post=post)

        with pytest.raises(IntegrityError):
            PostLikeFactory(user=user, post=post)

    def test_user_cannot_like_comment_twice(self, db):
        """User cannot like same comment twice."""
        user = UserFactory()
        comment = CommentFactory()
        CommentLikeFactory(user=user, comment=comment)

        with pytest.raises(IntegrityError):
            CommentLikeFactory(user=user, comment=comment)


class TestUserFollow:
    """Tests for UserFollow model."""

    def test_follow_creation(self, db):
        """UserFollow can be created."""
        follow = UserFollowFactory()
        assert follow.pk is not None
        assert follow.follower is not None
        assert follow.following is not None

    def test_follow_str_representation(self, db):
        """UserFollow __str__ shows follower and following."""
        follower = UserFactory(username="follower")
        following = UserFactory(username="following")
        follow = UserFollowFactory(follower=follower, following=following)
        assert str(follow) == "follower follows following"

    def test_cannot_follow_self(self, db):
        """User cannot follow themselves."""
        from synnovator.community.models import UserFollow

        user = UserFactory()
        follow = UserFollow(follower=user, following=user)

        with pytest.raises(ValidationError):
            follow.clean()

    def test_unique_follow_relationship(self, db):
        """User can only follow another user once."""
        follower = UserFactory()
        following = UserFactory()
        UserFollowFactory(follower=follower, following=following)

        with pytest.raises(IntegrityError):
            UserFollowFactory(follower=follower, following=following)

    def test_mutual_following(self, db):
        """Users can mutually follow each other."""
        user1 = UserFactory()
        user2 = UserFactory()

        follow1 = UserFollowFactory(follower=user1, following=user2)
        follow2 = UserFollowFactory(follower=user2, following=user1)

        assert follow1.pk is not None
        assert follow2.pk is not None

    def test_user_followers_count(self, db):
        """User can count followers."""
        user = UserFactory()
        UserFollowFactory(following=user)
        UserFollowFactory(following=user)
        UserFollowFactory(following=user)

        assert user.followers.count() == 3

    def test_user_following_count(self, db):
        """User can count following."""
        user = UserFactory()
        UserFollowFactory(follower=user)
        UserFollowFactory(follower=user)

        assert user.following.count() == 2


class TestReport:
    """Tests for Report model."""

    def test_post_report_creation(self, db):
        """Post report can be created."""
        report = PostReportFactory()
        assert report.pk is not None
        assert report.post is not None
        assert report.comment is None

    def test_comment_report_creation(self, db):
        """Comment report can be created."""
        report = CommentReportFactory()
        assert report.pk is not None
        assert report.comment is not None
        assert report.post is None

    def test_report_str_representation(self, db):
        """Report __str__ shows reporter and content type."""
        reporter = UserFactory(username="reporter")
        report = PostReportFactory(reporter=reporter, reason="spam")
        assert "reporter" in str(report)
        assert "post" in str(report)
        assert "Spam" in str(report)

    def test_report_reason_choices(self, db):
        """Report accepts valid reason choices."""
        reasons = ["spam", "harassment", "inappropriate", "misinformation", "copyright", "other"]
        for reason in reasons:
            report = PostReportFactory(reason=reason)
            assert report.reason == reason

    def test_report_status_choices(self, db):
        """Report accepts valid status choices."""
        statuses = ["pending", "reviewing", "action_taken", "dismissed"]
        for status in statuses:
            report = PostReportFactory(status=status)
            assert report.status == status

    def test_report_requires_post_or_comment(self, db):
        """Report must have either post or comment."""
        from synnovator.community.models import Report

        reporter = UserFactory()
        report = Report(reporter=reporter, post=None, comment=None, reason="spam")

        with pytest.raises(ValidationError):
            report.clean()

    def test_report_cannot_have_both(self, db):
        """Report cannot have both post and comment."""
        from synnovator.community.models import Report

        reporter = UserFactory()
        post = CommunityPostFactory()
        comment = CommentFactory()
        report = Report(reporter=reporter, post=post, comment=comment, reason="spam")

        with pytest.raises(ValidationError):
            report.clean()


# =============================================================================
# Team Management Tests
# =============================================================================


class TestTeamProfilePage:
    """Tests for TeamProfilePage model."""

    def test_team_creation(self, db):
        """TeamProfilePage can be created."""
        team = TeamProfilePageFactory()
        assert team.pk is not None
        assert team.title

    def test_team_creates_django_group(self, db):
        """TeamProfilePage creates associated Django Group on save."""
        team = TeamProfilePageFactory(title="Alpha Team", slug="alpha-team")
        team.refresh_from_db()

        assert team.django_group is not None
        assert team.django_group.name == "team_alpha-team"

    def test_team_add_member(self, db):
        """Team can add a member."""
        team = TeamProfilePageFactory()
        team.refresh_from_db()
        user = UserFactory()

        membership = team.add_member(user, role="hacker")

        assert membership.pk is not None
        assert membership.user == user
        assert membership.role == "hacker"
        assert team.is_member(user)

    def test_team_add_member_adds_to_group(self, db):
        """Adding a member also adds them to Django Group."""
        team = TeamProfilePageFactory()
        team.refresh_from_db()
        user = UserFactory()

        team.add_member(user, role="hacker")

        assert user.groups.filter(pk=team.django_group.pk).exists()

    def test_team_add_leader(self, db):
        """Team can add a leader."""
        team = TeamProfilePageFactory()
        team.refresh_from_db()
        user = UserFactory()

        membership = team.add_member(user, role="hacker", is_leader=True)

        assert membership.is_leader
        assert team.get_leader() == user

    def test_team_remove_member(self, db):
        """Team can remove a member."""
        team = TeamProfilePageFactory()
        team.refresh_from_db()
        user = UserFactory()

        team.add_member(user, role="hacker")
        assert team.is_member(user)

        team.remove_member(user)
        assert not team.is_member(user)

    def test_team_remove_member_removes_from_group(self, db):
        """Removing a member also removes them from Django Group."""
        team = TeamProfilePageFactory()
        team.refresh_from_db()
        user = UserFactory()

        team.add_member(user, role="hacker")
        team.remove_member(user)

        assert not user.groups.filter(pk=team.django_group.pk).exists()

    def test_cannot_remove_leader(self, db):
        """Cannot remove the team leader."""
        team = TeamProfilePageFactory()
        team.refresh_from_db()
        leader = UserFactory()

        team.add_member(leader, role="hacker", is_leader=True)

        with pytest.raises(ValueError):
            team.remove_member(leader)

    def test_team_member_count(self, db):
        """Team tracks member count."""
        team = TeamProfilePageFactory()
        team.refresh_from_db()

        assert team.get_member_count() == 0

        user1 = UserFactory()
        user2 = UserFactory()

        team.add_member(user1, is_leader=True)
        team.add_member(user2)

        assert team.get_member_count() == 2

    def test_team_can_add_member_check(self, db):
        """can_add_member respects max_members and is_open_for_members."""
        team = TeamProfilePageFactory(max_members=2, is_open_for_members=True)
        team.refresh_from_db()

        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()

        team.add_member(user1, is_leader=True)
        assert team.can_add_member()

        team.add_member(user2)
        assert not team.can_add_member()

        # Cannot add third member
        with pytest.raises(ValueError):
            team.add_member(user3)

    def test_team_closed_for_members(self, db):
        """Team can be closed for new members."""
        team = TeamProfilePageFactory(is_open_for_members=False)
        team.refresh_from_db()
        user = UserFactory()

        assert not team.can_add_member()

        with pytest.raises(ValueError):
            team.add_member(user)

    def test_cannot_add_duplicate_member(self, db):
        """Cannot add same user twice."""
        team = TeamProfilePageFactory()
        team.refresh_from_db()
        user = UserFactory()

        team.add_member(user, is_leader=True)

        with pytest.raises(ValueError):
            team.add_member(user)

    def test_user_can_edit_for_member(self, db):
        """Team member can edit team."""
        team = TeamProfilePageFactory()
        team.refresh_from_db()
        user = UserFactory()

        team.add_member(user)

        assert team.user_can_edit(user)

    def test_user_can_edit_for_non_member(self, db):
        """Non-member cannot edit team."""
        team = TeamProfilePageFactory()
        team.refresh_from_db()
        user = UserFactory()

        assert not team.user_can_edit(user)


class TestTeamMembership:
    """Tests for TeamMembership model."""

    def test_membership_creation(self, db):
        """TeamMembership can be created."""
        membership = TeamMembershipFactory()
        assert membership.pk is not None
        assert membership.team is not None
        assert membership.user is not None

    def test_membership_str_representation(self, db):
        """TeamMembership __str__ includes user name and role."""
        user = UserFactory(first_name="John", last_name="Doe")
        team = TeamProfilePageFactory()
        membership = TeamMembershipFactory(team=team, user=user, role="hacker")

        assert "John Doe" in str(membership)
        assert "Hacker" in str(membership)

    def test_membership_role_choices(self, db):
        """TeamMembership accepts valid role choices."""
        roles = ["hacker", "hipster", "hustler", "mentor", "member"]
        team = TeamProfilePageFactory()

        for role in roles:
            user = UserFactory()
            membership = TeamMembershipFactory(team=team, user=user, role=role)
            assert membership.role == role

    def test_membership_unique_per_team(self, db):
        """User can only be member of a team once."""
        team = TeamProfilePageFactory()
        team.refresh_from_db()
        user = UserFactory()

        team.add_member(user, is_leader=True)

        with pytest.raises(ValueError):
            team.add_member(user)
