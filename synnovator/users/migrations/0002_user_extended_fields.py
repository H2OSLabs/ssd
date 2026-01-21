# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='preferred_role',
            field=models.CharField(blank=True, choices=[('hacker', 'Hacker (Engineer)'), ('hipster', 'Hipster (Designer/UX)'), ('hustler', 'Hustler (Business/Marketing)'), ('mentor', 'Mentor'), ('any', 'Flexible')], help_text='Preferred team role', max_length=50),
        ),
        migrations.AddField(
            model_name='user',
            name='bio',
            field=models.TextField(blank=True, help_text='Short bio for team matching', max_length=500),
        ),
        migrations.AddField(
            model_name='user',
            name='skills',
            field=models.JSONField(blank=True, default=list, help_text="List of skills (e.g., ['Python', 'React', 'ML'])"),
        ),
        migrations.AddField(
            model_name='user',
            name='xp_points',
            field=models.PositiveIntegerField(default=0, help_text='Total experience points earned'),
        ),
        migrations.AddField(
            model_name='user',
            name='reputation_score',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Quality metric based on submissions and peer ratings', max_digits=6),
        ),
        migrations.AddField(
            model_name='user',
            name='level',
            field=models.PositiveIntegerField(default=1, help_text='User level (derived from XP)'),
        ),
        migrations.AddField(
            model_name='user',
            name='profile_completed',
            field=models.BooleanField(default=False, help_text='User has completed profile setup'),
        ),
        migrations.AddField(
            model_name='user',
            name='onboarding_completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='is_seeking_team',
            field=models.BooleanField(default=False, help_text='Show in team formation matching'),
        ),
        migrations.AddField(
            model_name='user',
            name='notification_preferences',
            field=models.JSONField(blank=True, default=dict, help_text='Email/push notification settings'),
        ),
    ]
