from django.db import models
from django.conf import settings


class Team(models.Model):
    """
    Represents a team participating in a hackathon.
    """

    hackathon = models.ForeignKey(
        'HackathonPage',
        on_delete=models.CASCADE,
        related_name='teams'
    )

    name = models.CharField(
        max_length=200,
        help_text="Team name"
    )

    slug = models.SlugField(
        max_length=200,
        help_text="URL-friendly team identifier"
    )

    tagline = models.CharField(
        max_length=500,
        blank=True,
        help_text="Short team description"
    )

    # Team composition
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='TeamMember',
        related_name='hackathon_teams'
    )

    # Scoring
    final_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.0,
        help_text="Aggregated score from verification"
    )

    technical_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.0
    )

    commercial_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.0
    )

    operational_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.0
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('forming', 'Forming'),
            ('ready', 'Ready'),
            ('submitted', 'Submitted'),
            ('verified', 'Verified'),
            ('advanced', 'Advanced to Next Round'),
            ('eliminated', 'Eliminated'),
            ('disqualified', 'Disqualified'),
        ],
        default='forming'
    )

    is_seeking_members = models.BooleanField(
        default=True,
        help_text="Show in team formation page"
    )

    # Advancement tracking
    elimination_reason = models.TextField(
        blank=True,
        help_text="Reason for elimination or disqualification"
    )

    current_round = models.PositiveIntegerField(
        default=1,
        help_text="Current competition round"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['hackathon', 'slug']]
        ordering = ['-final_score', 'name']

    def __str__(self):
        return f"{self.name} ({self.hackathon.title})"

    def get_leader(self):
        """Get team leader (first member with is_leader=True)"""
        return self.membership.filter(is_leader=True).first()

    def has_required_roles(self):
        """Check if team meets hackathon's required role composition"""
        required = set(self.hackathon.required_roles)
        current = set(self.membership.values_list('role', flat=True))
        return required.issubset(current)

    def can_add_member(self):
        """Check if team can accept new members"""
        return (
            self.members.count() < self.hackathon.max_team_size and
            self.status == 'forming'
        )

    def update_scores(self):
        """Update aggregated scores from judge scores"""
        from django.db.models import Avg

        # Get all submissions for this team
        submissions = self.submissions.filter(verification_status='verified')

        # Calculate average scores across all judge scores for all submissions
        for submission in submissions:
            judge_scores = submission.judge_scores.all()
            if judge_scores.exists():
                avg_scores = judge_scores.aggregate(
                    tech=Avg('technical_score'),
                    comm=Avg('commercial_score'),
                    oper=Avg('operational_score')
                )

                # Update team scores (average across all submissions)
                self.technical_score = avg_scores['tech'] or 0.0
                self.commercial_score = avg_scores['comm'] or 0.0
                self.operational_score = avg_scores['oper'] or 0.0
                self.final_score = (
                    self.technical_score +
                    self.commercial_score +
                    self.operational_score
                ) / 3

        self.save()


class TeamMember(models.Model):
    """
    Through model for Team-User M2M relationship.
    Tracks role, contribution, and leadership.
    """

    team = models.ForeignKey(
        'Team',
        on_delete=models.CASCADE,
        related_name='membership'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='team_memberships'
    )

    role = models.CharField(
        max_length=50,
        choices=[
            ('hacker', 'Hacker (Engineer)'),
            ('hipster', 'Hipster (Designer/UX)'),
            ('hustler', 'Hustler (Business/Marketing)'),
            ('mentor', 'Mentor'),
        ],
        help_text="Team role"
    )

    is_leader = models.BooleanField(
        default=False,
        help_text="Team captain/leader"
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['team', 'user']]
        ordering = ['-is_leader', 'joined_at']

    def __str__(self):
        leader = " (Leader)" if self.is_leader else ""
        return f"{self.user.get_full_name()} - {self.get_role_display()}{leader}"
