from django.db import models
from wagtail.fields import RichTextField


class Quest(models.Model):
    """
    Represents a Dojo challenge that can be standalone or hackathon-specific.
    Quests award XP and serve as skill verification.
    """

    title = models.CharField(
        max_length=200,
        help_text="Quest name"
    )

    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text="URL-friendly identifier"
    )

    description = RichTextField(
        help_text="Challenge description and objectives"
    )

    # Quest type and difficulty
    quest_type = models.CharField(
        max_length=20,
        choices=[
            ('technical', 'Technical (Hacker)'),
            ('commercial', 'Commercial (Hustler)'),
            ('operational', 'Operational (Hipster)'),
            ('mixed', 'Mixed'),
        ],
        default='technical'
    )

    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert'),
        ],
        default='intermediate'
    )

    # Gamification
    xp_reward = models.PositiveIntegerField(
        default=100,
        help_text="XP awarded upon completion"
    )

    estimated_time_minutes = models.PositiveIntegerField(
        default=60,
        help_text="Estimated completion time"
    )

    # Association
    hackathon = models.ForeignKey(
        'HackathonPage',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='quests',
        help_text="If set, quest is specific to this hackathon"
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Quest is available for attempts"
    )

    # Metadata
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Skill tags (e.g., ['python', 'machine-learning', 'api'])"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Quest"
        verbose_name_plural = "Quests"

    def __str__(self):
        return f"{self.title} ({self.get_difficulty_display()})"

    def get_completion_rate(self):
        """Calculate percentage of users who completed this quest"""
        total_attempts = self.submissions.count()
        if total_attempts == 0:
            return 0
        completed = self.submissions.filter(verification_status='passed').count()
        return (completed / total_attempts) * 100
