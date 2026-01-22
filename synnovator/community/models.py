"""
Community and social interaction models.
Implements P1 social features: posts, comments, likes, follows, and content moderation.
Implements team management with TeamProfilePage and Django Group integration.
"""
from django.contrib.auth.models import Group
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.models import Orderable, Page
from wagtail.snippets.models import register_snippet
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.documents.blocks import DocumentChooserBlock

from synnovator.utils.models import BasePage


@register_snippet
class CommunityPost(models.Model):
    """
    User-generated content posts in the community.
    Supports moderation workflow for content management.
    """

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_posts',
        verbose_name=_("Author")
    )

    title = models.CharField(
        max_length=200,
        verbose_name=_("Title"),
        help_text=_("Post title")
    )

    content = RichTextField(
        verbose_name=_("Content"),
        help_text=_("Post content")
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', _('Draft')),
            ('published', _('Published')),
            ('flagged', _('Flagged for Review')),
            ('removed', _('Removed')),
        ],
        default='draft',
        verbose_name=_("Status"),
        db_index=True
    )

    # Related hackathon (optional - posts can be standalone or hackathon-specific)
    hackathon = models.ForeignKey(
        'hackathons.HackathonPage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='community_posts',
        verbose_name=_("Related Hackathon"),
        help_text=_("Link post to a specific hackathon (optional)")
    )

    # Moderation
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='moderated_community_posts',
        verbose_name=_("Moderated By")
    )

    moderation_notes = models.TextField(
        blank=True,
        verbose_name=_("Moderation Notes"),
        help_text=_("Internal notes for moderation team")
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )

    panels = [
        FieldPanel('author'),
        FieldPanel('title'),
        FieldPanel('content'),
        FieldPanel('hackathon'),
        FieldPanel('status'),
        FieldPanel('moderation_notes'),
    ]

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Community Post")
        verbose_name_plural = _("Community Posts")
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['hackathon', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} by {self.author.username}"

    def get_like_count(self):
        """Get total number of likes"""
        return self.likes.count()

    def get_comment_count(self):
        """Get total number of comments"""
        return self.comments.count()


class Comment(models.Model):
    """
    Comments on community posts.
    Supports nested replies via parent field.
    """

    post = models.ForeignKey(
        CommunityPost,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_("Post")
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_("Author")
    )

    # Nested comments support
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies',
        verbose_name=_("Parent Comment"),
        help_text=_("Reply to another comment (optional)")
    )

    content = models.TextField(
        max_length=2000,
        verbose_name=_("Content")
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('visible', _('Visible')),
            ('hidden', _('Hidden')),
            ('flagged', _('Flagged')),
        ],
        default='visible',
        verbose_name=_("Status"),
        db_index=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )

    class Meta:
        ordering = ['created_at']
        verbose_name = _("Comment")
        verbose_name_plural = _("Comments")
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"

    def get_like_count(self):
        """Get total number of likes"""
        return self.likes.count()


class Like(models.Model):
    """
    Likes for posts and comments.
    Uses polymorphic pattern to support both content types.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name=_("User")
    )

    # Polymorphic relationships - user can like either a post or a comment
    post = models.ForeignKey(
        CommunityPost,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name=_("Post")
    )

    comment = models.ForeignKey(
        Comment,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name=_("Comment")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )

    class Meta:
        # User can only like a specific post/comment once
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'post'],
                condition=models.Q(post__isnull=False),
                name='unique_user_post_like'
            ),
            models.UniqueConstraint(
                fields=['user', 'comment'],
                condition=models.Q(comment__isnull=False),
                name='unique_user_comment_like'
            ),
            models.CheckConstraint(
                check=(
                    models.Q(post__isnull=False, comment__isnull=True) |
                    models.Q(post__isnull=True, comment__isnull=False)
                ),
                name='like_either_post_or_comment'
            ),
        ]
        verbose_name = _("Like")
        verbose_name_plural = _("Likes")
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['comment', '-created_at']),
        ]

    def __str__(self):
        if self.post:
            return f"{self.user.username} likes post: {self.post.title}"
        elif self.comment:
            return f"{self.user.username} likes comment by {self.comment.author.username}"
        return f"Like by {self.user.username}"

    def clean(self):
        """Validate that exactly one of post or comment is set"""
        from django.core.exceptions import ValidationError
        if not (bool(self.post) ^ bool(self.comment)):
            raise ValidationError(_("Like must be for either a post or a comment, not both or neither"))


class UserFollow(models.Model):
    """
    User follow/follower relationships.
    Implements social graph for user connections.
    """

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name=_("Follower"),
        help_text=_("User who is following")
    )

    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name=_("Following"),
        help_text=_("User being followed")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )

    class Meta:
        unique_together = [['follower', 'following']]
        verbose_name = _("User Follow")
        verbose_name_plural = _("User Follows")
        indexes = [
            models.Index(fields=['follower', '-created_at']),
            models.Index(fields=['following', '-created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(follower=models.F('following')),
                name='prevent_self_follow'
            ),
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"

    def clean(self):
        """Validate that users don't follow themselves"""
        from django.core.exceptions import ValidationError
        if self.follower == self.following:
            raise ValidationError(_("Users cannot follow themselves"))


@register_snippet
class Report(models.Model):
    """
    Content reporting system for community moderation.
    Users can report inappropriate posts or comments.
    """

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_made',
        verbose_name=_("Reporter")
    )

    # Polymorphic - can report either a post or comment
    post = models.ForeignKey(
        CommunityPost,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_("Reported Post")
    )

    comment = models.ForeignKey(
        Comment,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_("Reported Comment")
    )

    reason = models.CharField(
        max_length=50,
        choices=[
            ('spam', _('Spam')),
            ('harassment', _('Harassment')),
            ('inappropriate', _('Inappropriate Content')),
            ('misinformation', _('Misinformation')),
            ('copyright', _('Copyright Violation')),
            ('other', _('Other')),
        ],
        verbose_name=_("Reason")
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Additional details about the report")
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', _('Pending Review')),
            ('reviewing', _('Under Review')),
            ('action_taken', _('Action Taken')),
            ('dismissed', _('Dismissed')),
        ],
        default='pending',
        verbose_name=_("Status"),
        db_index=True
    )

    # Moderation
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reports_reviewed',
        verbose_name=_("Reviewed By")
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Reviewed At")
    )

    action_taken = models.TextField(
        blank=True,
        verbose_name=_("Action Taken"),
        help_text=_("What action was taken in response to this report")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )

    panels = [
        FieldPanel('reporter'),
        FieldPanel('post'),
        FieldPanel('comment'),
        FieldPanel('reason'),
        FieldPanel('description'),
        FieldPanel('status'),
        FieldPanel('reviewed_by'),
        FieldPanel('action_taken'),
    ]

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Report")
        verbose_name_plural = _("Reports")
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['reporter', '-created_at']),
            models.Index(fields=['reviewed_by', '-reviewed_at']),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(post__isnull=False, comment__isnull=True) |
                    models.Q(post__isnull=True, comment__isnull=False)
                ),
                name='report_either_post_or_comment'
            ),
        ]

    def __str__(self):
        content_type = "post" if self.post else "comment"
        return f"Report by {self.reporter.username} - {content_type} ({self.get_reason_display()})"

    def clean(self):
        """Validate that exactly one of post or comment is set"""
        from django.core.exceptions import ValidationError
        if not (bool(self.post) ^ bool(self.comment)):
            raise ValidationError(_("Report must be for either a post or a comment, not both or neither"))


# =============================================================================
# Team Management Models
# =============================================================================


class TeamIndexPage(BasePage):
    """
    Index page for listing all teams.
    Follows Wagtail Index Page pattern.
    """

    introduction = RichTextField(
        blank=True,
        features=["bold", "italic", "link"],
        help_text=_("Introduction text displayed at the top of the teams listing page")
    )

    subpage_types = ['community.TeamProfilePage']
    max_count = 1

    content_panels = BasePage.content_panels + [
        FieldPanel('introduction'),
    ]

    class Meta:
        verbose_name = _("Team Index Page")
        verbose_name_plural = _("Team Index Pages")

    def get_context(self, request, *args, **kwargs):
        """Add teams queryset to template context"""
        context = super().get_context(request, *args, **kwargs)
        teams = TeamProfilePage.objects.live().public().order_by('-first_published_at')
        context['teams'] = teams
        return context


class TeamProfilePage(BasePage):
    """
    Team profile page that integrates with Django's Group permission system.

    Creating a team:
    - Creates a TeamProfilePage under TeamIndexPage
    - Automatically creates a Django Group named 'team_{slug}'
    - Creator becomes team leader and is added to the Group

    Joining a team:
    - Creates a TeamMembership relation
    - Adds user to the associated Django Group

    Permissions:
    - Team members can edit team content (via Group permissions)
    - Only leader can manage membership
    """

    # Associated Django Group (auto-created)
    django_group = models.OneToOneField(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name='team_profile',
        help_text=_("Auto-created Django Group for team permissions")
    )

    # Team information
    tagline = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Tagline"),
        help_text=_("Short team description or motto")
    )

    logo = models.ForeignKey(
        'images.CustomImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Logo")
    )

    # Team settings
    is_open_for_members = models.BooleanField(
        default=True,
        verbose_name=_("Open for New Members"),
        help_text=_("Show in team formation and accept join requests")
    )

    max_members = models.PositiveIntegerField(
        default=10,
        verbose_name=_("Maximum Members"),
        help_text=_("Maximum number of team members allowed")
    )

    # Contact and links
    website = models.URLField(
        blank=True,
        verbose_name=_("Website")
    )

    github_url = models.URLField(
        blank=True,
        verbose_name=_("GitHub URL")
    )

    # Team content
    body = StreamField([
        ('heading', blocks.CharBlock(form_classname="title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
    ], blank=True, use_json_field=True)

    # Page configuration
    parent_page_types = ['community.TeamIndexPage']
    subpage_types = []

    content_panels = BasePage.content_panels + [
        FieldPanel('tagline'),
        FieldPanel('logo'),
        FieldPanel('body'),
        MultiFieldPanel([
            FieldPanel('is_open_for_members'),
            FieldPanel('max_members'),
        ], heading=_("Membership Settings")),
        MultiFieldPanel([
            FieldPanel('website'),
            FieldPanel('github_url'),
        ], heading=_("Links")),
        InlinePanel('memberships', label=_("Team Members")),
    ]

    class Meta:
        verbose_name = _("Team Profile")
        verbose_name_plural = _("Team Profiles")

    def get_context(self, request, *args, **kwargs):
        """Add membership context for the current user"""
        context = super().get_context(request, *args, **kwargs)
        user = request.user

        is_member = False
        is_leader = False
        user_membership = None

        if user.is_authenticated:
            user_membership = self.memberships.filter(user=user).first()
            if user_membership:
                is_member = True
                is_leader = user_membership.is_leader

        context['is_member'] = is_member
        context['is_leader'] = is_leader
        context['user_membership'] = user_membership
        return context

    def save(self, *args, **kwargs):
        """Create associated Django Group on first save"""
        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new and not self.django_group:
            group_name = f"team_{self.slug}"
            group, created = Group.objects.get_or_create(name=group_name)
            self.django_group = group
            # Use update to avoid triggering another save
            TeamProfilePage.objects.filter(pk=self.pk).update(django_group=group)

    def delete(self, *args, **kwargs):
        """Clean up Django Group when team is deleted"""
        if self.django_group:
            self.django_group.delete()
        super().delete(*args, **kwargs)

    def get_leader(self):
        """Get team leader"""
        leader_membership = self.memberships.filter(is_leader=True).first()
        return leader_membership.user if leader_membership else None

    def get_member_count(self):
        """Get current number of members"""
        return self.memberships.count()

    def can_add_member(self):
        """Check if team can accept new members"""
        return (
            self.is_open_for_members and
            self.get_member_count() < self.max_members
        )

    def add_member(self, user, role='member', is_leader=False):
        """
        Add a user to the team.

        Creates TeamMembership and adds user to Django Group.
        """
        if not self.can_add_member() and not is_leader:
            raise ValueError(_("Team is not accepting new members"))

        # Check if already a member
        if self.memberships.filter(user=user).exists():
            raise ValueError(_("User is already a team member"))

        # Create membership
        membership = TeamMembership.objects.create(
            team=self,
            user=user,
            role=role,
            is_leader=is_leader
        )

        # Add to Django Group
        if self.django_group:
            user.groups.add(self.django_group)

        return membership

    def remove_member(self, user):
        """
        Remove a user from the team.

        Removes TeamMembership and removes user from Django Group.
        """
        membership = self.memberships.filter(user=user).first()
        if not membership:
            raise ValueError(_("User is not a team member"))

        if membership.is_leader:
            raise ValueError(_("Cannot remove team leader"))

        # Remove from Django Group
        if self.django_group:
            user.groups.remove(self.django_group)

        membership.delete()

    def is_member(self, user):
        """Check if user is a team member"""
        if not user.is_authenticated:
            return False
        return self.memberships.filter(user=user).exists()

    def user_can_edit(self, user):
        """Check if user can edit team content"""
        if not user.is_authenticated:
            return False
        return self.is_member(user) or user.is_superuser


class TeamMembership(Orderable):
    """
    Through model for team membership.
    Tracks role, contribution, and leadership.
    """

    team = ParentalKey(
        'TeamProfilePage',
        on_delete=models.CASCADE,
        related_name='memberships'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='team_memberships_new',
        verbose_name=_("User")
    )

    role = models.CharField(
        max_length=50,
        choices=[
            ('hacker', _('Hacker (Engineer)')),
            ('hipster', _('Hipster (Designer/UX)')),
            ('hustler', _('Hustler (Business/Marketing)')),
            ('mentor', _('Mentor')),
            ('member', _('Member')),
        ],
        default='member',
        verbose_name=_("Role"),
        help_text=_("Team role")
    )

    is_leader = models.BooleanField(
        default=False,
        verbose_name=_("Is Leader"),
        help_text=_("Team captain/leader")
    )

    joined_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Joined At")
    )

    panels = [
        FieldPanel('user'),
        FieldPanel('role'),
        FieldPanel('is_leader'),
    ]

    class Meta:
        unique_together = [['team', 'user']]
        ordering = ['-is_leader', 'joined_at']
        verbose_name = _("Team Membership")
        verbose_name_plural = _("Team Memberships")

    def __str__(self):
        leader = " (Leader)" if self.is_leader else ""
        return f"{self.user.get_full_name() or self.user.username} - {self.get_role_display()}{leader}"

    def save(self, *args, **kwargs):
        """Ensure user is in Django Group when membership is saved"""
        super().save(*args, **kwargs)
        if self.team.django_group:
            self.user.groups.add(self.team.django_group)

    def delete(self, *args, **kwargs):
        """Remove user from Django Group when membership is deleted"""
        if self.team.django_group:
            self.user.groups.remove(self.team.django_group)
        super().delete(*args, **kwargs)
