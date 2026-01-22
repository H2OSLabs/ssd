from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _

from synnovator.hackathons.models import Team, Submission
from synnovator.notifications.models import NOTIFICATION_TYPES

User = get_user_model()


def user_profile(request, username):
    """
    User profile page view.

    Provides full context for templates/pages/user_profile_page.html
    """
    profile_user = get_object_or_404(User, username=username)

    # Get team memberships
    from synnovator.hackathons.models import TeamMember

    memberships = TeamMember.objects.filter(user=profile_user).select_related(
        'team', 'team__hackathon'
    )

    # Separate current and past teams based on hackathon status
    current_teams = []
    past_teams = []
    for membership in memberships:
        if membership.team.hackathon.status in ['upcoming', 'registration_open', 'in_progress']:
            current_teams.append(membership.team)
        else:
            past_teams.append(membership.team)

    # Get recent submissions
    recent_submissions = Submission.objects.filter(
        user=profile_user
    ).select_related('quest', 'hackathon').order_by('-submitted_at')[:5]

    # Calculate stats
    quests_completed = Submission.objects.filter(
        user=profile_user,
        verification_status='verified',
        quest__isnull=False
    ).count()

    teams_joined = memberships.count()

    hackathons_participated = memberships.values('team__hackathon').distinct().count()

    # Build skills list with verification status
    verified_skills = set(profile_user.get_verified_skills())
    skills = []
    for skill in profile_user.skills or []:
        skills.append({
            'name': skill,
            'is_verified': skill.lower() in [s.lower() for s in verified_skills]
        })
    # Add verified skills not in profile
    for skill in verified_skills:
        if skill.lower() not in [s['name'].lower() for s in skills]:
            skills.append({
                'name': skill,
                'is_verified': True
            })

    # Build activity history from submissions and team memberships
    activity_history = []
    for submission in recent_submissions:
        target = submission.quest.title if submission.quest else (
            submission.hackathon.title if submission.hackathon else "Unknown"
        )
        activity_history.append({
            'action': f"Submitted to {target}",
            'date': submission.submitted_at
        })
    for membership in memberships.order_by('-joined_at')[:5]:
        activity_history.append({
            'action': f"Joined team {membership.team.name}",
            'date': membership.joined_at
        })
    activity_history.sort(key=lambda x: x['date'], reverse=True)

    # Build projects from hackathon submissions
    projects = []
    hackathon_submissions = Submission.objects.filter(
        Q(user=profile_user) | Q(team__members=profile_user),
        hackathon__isnull=False,
        verification_status='verified'
    ).select_related('hackathon').distinct()

    for sub in hackathon_submissions[:5]:
        projects.append({
            'name': sub.hackathon.title,
            'description': sub.description[:200] if sub.description else '',
            'url': sub.submission_url or None,
            'tech_stack': sub.hackathon.required_skills if hasattr(sub.hackathon, 'required_skills') else []
        })

    # Calculate XP for next level (100 XP per level)
    current_level_xp = (profile_user.level - 1) * 100
    next_level_xp = profile_user.level * 100
    xp_for_next_level = next_level_xp

    context = {
        'profile_user': profile_user,
        'current_teams': current_teams,
        'past_teams': past_teams,
        'recent_submissions': recent_submissions,
        'skills': skills,
        'activity_history': activity_history[:10],
        'projects': projects,
        'stats': {
            'hackathons_participated': hackathons_participated,
            'quests_completed': quests_completed,
            'teams_joined': teams_joined,
        },
    }

    # Add computed fields to profile_user for template compatibility
    profile_user.xp = profile_user.xp_points
    profile_user.xp_for_next_level = xp_for_next_level
    profile_user.role = profile_user.preferred_role
    profile_user.reputation = float(profile_user.reputation_score)
    profile_user.quests_completed = quests_completed
    profile_user.teams_joined = teams_joined
    profile_user.seeking_team = profile_user.is_seeking_team
    profile_user.skills = skills
    profile_user.current_teams = current_teams
    profile_user.past_teams = past_teams
    profile_user.recent_submissions = recent_submissions
    profile_user.activity_history = activity_history[:10]
    profile_user.projects = projects

    return render(request, 'pages/user_profile_page.html', context)


@login_required
def notification_preferences(request):
    """
    User notification preferences page.

    Allows users to configure per-type notification settings for in-app and email channels.
    """
    if request.method == 'POST':
        # Build preferences dict from form data
        prefs = {
            'in_app': request.POST.get('global_in_app') == 'on',
            'email': request.POST.get('global_email') == 'on',
            'types': {}
        }

        # Process each notification type
        for type_key, _ in NOTIFICATION_TYPES:
            prefs['types'][type_key] = {
                'in_app': request.POST.get(f'{type_key}_in_app') == 'on',
                'email': request.POST.get(f'{type_key}_email') == 'on',
            }

        # Save preferences
        request.user.notification_preferences = prefs
        request.user.save(update_fields=['notification_preferences'])

        messages.success(request, _("Notification preferences saved."))
        return redirect('users:notification_preferences')

    # GET request - display form
    preferences = request.user.notification_preferences or {}
    types_prefs = preferences.get('types', {})

    # Pre-process notification types with their current preference state
    processed_types = []
    for type_key, type_label in NOTIFICATION_TYPES:
        type_pref = types_prefs.get(type_key, {})
        processed_types.append({
            'key': type_key,
            'label': type_label,
            'in_app': type_pref.get('in_app', True),  # Default to enabled
            'email': type_pref.get('email', False),  # Default to disabled
        })

    context = {
        'notification_types': processed_types,
        'preferences': preferences,
    }

    return render(request, 'users/notification_preferences.html', context)
