"""
Community and social interaction models.
Implements P1 social features: posts, comments, likes, follows, and content moderation.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet


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
