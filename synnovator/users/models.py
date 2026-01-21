from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Extended user model with hackathon-specific fields.
    """

    # Profile
    preferred_role = models.CharField(
        max_length=50,
        choices=[
            ('hacker', 'Hacker (Engineer)'),
            ('hipster', 'Hipster (Designer/UX)'),
            ('hustler', 'Hustler (Business/Marketing)'),
            ('mentor', 'Mentor'),
            ('any', 'Flexible'),
        ],
        blank=True,
        help_text="Preferred team role"
    )

    bio = models.TextField(
        max_length=500,
        blank=True,
        help_text="Short bio for team matching"
    )

    skills = models.JSONField(
        default=list,
        blank=True,
        help_text="List of skills (e.g., ['Python', 'React', 'ML'])"
    )

    # Gamification
    xp_points = models.PositiveIntegerField(
        default=0,
        help_text="Total experience points earned"
    )

    reputation_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.0,
        help_text="Quality metric based on submissions and peer ratings"
    )

    level = models.PositiveIntegerField(
        default=1,
        help_text="User level (derived from XP)"
    )

    # Onboarding
    profile_completed = models.BooleanField(
        default=False,
        help_text="User has completed profile setup"
    )

    onboarding_completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # Preferences
    is_seeking_team = models.BooleanField(
        default=False,
        help_text="Show in team formation matching"
    )

    notification_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="Email/push notification settings"
    )

    class Meta(AbstractUser.Meta):
        swappable = 'AUTH_USER_MODEL'

    def calculate_level(self):
        """Calculate level from XP (100 XP per level)"""
        return (self.xp_points // 100) + 1

    def award_xp(self, points, reason=""):
        """Add XP and recalculate level"""
        self.xp_points += points
        self.level = self.calculate_level()
        self.save()

    def get_verified_skills(self):
        """Return skills verified through quest completions"""
        from synnovator.hackathons.models import Submission

        completed_quests = Submission.objects.filter(
            user=self,
            quest__isnull=False,
            verification_status='verified'
        ).select_related('quest')

        skills = set()
        for submission in completed_quests:
            if submission.quest and submission.quest.tags:
                skills.update(submission.quest.tags)
        return list(skills)
