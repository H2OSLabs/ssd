from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse
from django.utils.text import slugify
from django.utils.translation import gettext as _, get_language
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Count, Q, Prefetch

from .models import (
    HackathonPage, HackathonIndexPage, Team, Quest, Phase, TeamMember,
    Submission, SubmissionPage, SubmissionIndexPage, QuestIndexPage, TeamRegistration
)
from synnovator.community.models import TeamProfilePage

User = get_user_model()


def hackathon_index(request):
    """Redirect to main HackathonIndexPage (filter_mode='all')"""
    index_page = HackathonIndexPage.objects.live().filter(filter_mode='all').first()
    if not index_page:
        index_page = HackathonIndexPage.objects.live().first()
    if not index_page:
        index_page = HackathonIndexPage.objects.first()

    if index_page:
        return redirect(index_page.url)
    messages.info(request, 'Hackathons page not found. Please create a Hackathon Index Page in Wagtail admin.')
    return redirect('/')


def hackathon_in_progress(request):
    """Redirect to in-progress HackathonIndexPage (filter_mode='in_progress')"""
    index_page = HackathonIndexPage.objects.live().filter(filter_mode='in_progress').first()
    if not index_page:
        # Fall back to main index with filter param
        index_page = HackathonIndexPage.objects.live().first()
        if index_page:
            return redirect(f'{index_page.url}?status=in_progress')
    if not index_page:
        index_page = HackathonIndexPage.objects.first()

    if index_page:
        return redirect(index_page.url)
    messages.info(request, 'Hackathons page not found. Please create a Hackathon Index Page in Wagtail admin.')
    return redirect('/')


def hackathon_list(request):
    """Redirect to HackathonIndexPage (Wagtail page) - legacy support"""
    # Try to find a live page first
    index_page = HackathonIndexPage.objects.live().first()
    # If no live page, try to find any page (for development/testing)
    if not index_page:
        index_page = HackathonIndexPage.objects.first()

    if index_page:
        return redirect(index_page.url)
    # Fallback if no index page exists
    messages.info(request, 'Hackathons page not found. Please create a Hackathon Index Page in Wagtail admin.')
    return redirect('/')


def team_list(request, hackathon_slug=None):
    """List all teams with filtering and pagination."""
    teams = Team.objects.select_related('hackathon').prefetch_related(
        Prefetch('membership', queryset=TeamMember.objects.select_related('user'))
    ).annotate(
        members_count=Count('membership')
    )

    # Filter by hackathon slug (from URL path) or hackathon id (from query param)
    hackathon = None
    if hackathon_slug:
        hackathon = get_object_or_404(HackathonPage, slug=hackathon_slug)
        teams = teams.filter(hackathon=hackathon)
    else:
        hackathon_id = request.GET.get('hackathon')
        if hackathon_id:
            teams = teams.filter(hackathon_id=hackathon_id)

    status = request.GET.get('status')
    if status:
        teams = teams.filter(status=status)

    is_recruiting = request.GET.get('recruiting')
    if is_recruiting:
        teams = teams.filter(is_seeking_members=True)

    # Pagination
    paginator = Paginator(teams, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get hackathons for filter dropdown
    hackathons = HackathonPage.objects.filter(
        status__in=['upcoming', 'registration_open', 'in_progress']
    ).values('id', 'title')

    return render(request, 'hackathons/team_list.html', {
        'teams': page_obj,
        'page_obj': page_obj,
        'hackathons': hackathons,
        'hackathon': hackathon,
        'filters': {
            'hackathon': hackathon.id if hackathon else hackathon_id,
            'status': status,
            'recruiting': is_recruiting,
        }
    })


def team_detail(request, slug):
    """
    Team detail page view.

    Provides full context for templates/pages/team_detail_page.html
    """
    team = get_object_or_404(
        Team.objects.select_related('hackathon').prefetch_related(
            Prefetch(
                'membership',
                queryset=TeamMember.objects.select_related('user').order_by('-is_leader', 'joined_at')
            ),
            'submissions'
        ),
        slug=slug
    )

    # Build members list with additional info
    members = team.membership.all()

    # Get submissions
    submissions = team.submissions.select_related('quest', 'hackathon').order_by('-submitted_at')

    # Build activity log from submissions and membership changes
    activity_log = []
    for submission in submissions[:10]:
        target = submission.quest.title if submission.quest else (
            submission.hackathon.title if submission.hackathon else "Unknown"
        )
        activity_log.append({
            'timestamp': submission.submitted_at,
            'action': f"submitted to {target}",
            'user': submission.user or (submission.team.get_leader().user if submission.team and submission.team.get_leader() else None)
        })

    for membership in members:
        activity_log.append({
            'timestamp': membership.joined_at,
            'action': f"joined the team as {membership.get_role_display()}",
            'user': membership.user
        })

    activity_log.sort(key=lambda x: x['timestamp'], reverse=True)

    # Calculate stats
    stats = {
        'members_count': members.count(),
        'submissions_count': submissions.count(),
        'total_score': float(team.final_score) if team.final_score else 0,
        'score_breakdown': {
            'technical': float(team.technical_score) if team.technical_score else 0,
            'commercial': float(team.commercial_score) if team.commercial_score else 0,
            'operational': float(team.operational_score) if team.operational_score else 0,
        }
    }

    # Determine if user can join
    user_can_join = False
    if request.user.is_authenticated:
        is_member = team.members.filter(id=request.user.id).exists()
        user_can_join = not is_member and team.can_add_member()

    # Build hackathon info for template
    hackathon_info = None
    if team.hackathon:
        hackathon_info = {
            'name': team.hackathon.title,
            'start_date': team.hackathon.start_date if hasattr(team.hackathon, 'start_date') else None,
            'end_date': team.hackathon.end_date if hasattr(team.hackathon, 'end_date') else None,
            'status': team.hackathon.status,
        }

    # Map status for template compatibility
    status_mapping = {
        'forming': 'recruiting',
        'ready': 'formed',
        'submitted': 'submitted',
        'verified': 'verified',
    }
    template_status = status_mapping.get(team.status, team.status)

    context = {
        'team': team,
        'members': members,
        'submissions': submissions,
        'activity_log': activity_log,
        'stats': stats,
        'user_can_join': user_can_join,
    }

    # Add template-compatible attributes to team
    team.status = template_status
    team.members = members
    team.hackathon_info = hackathon_info
    team.submissions = submissions
    team.activity_log = activity_log
    team.stats = stats
    team.is_recruiting = team.is_seeking_members
    team.user_can_join = user_can_join

    # Create hackathon object for template
    if hackathon_info:
        class HackathonContext:
            pass
        h = HackathonContext()
        h.name = hackathon_info['name']
        h.start_date = hackathon_info['start_date']
        h.end_date = hackathon_info['end_date']
        h.status = hackathon_info['status']
        team.hackathon = h

    return render(request, 'pages/team_detail_page.html', context)


def team_formation(request):
    """
    Team formation page view.

    Provides full context for templates/pages/team_formation_page.html
    Shows users seeking teams and teams seeking members.
    """
    # Parse filters
    clear = request.GET.get('clear')
    if clear:
        return redirect('hackathons:team_formation')

    filter_roles = request.GET.getlist('roles')
    filter_skills = request.GET.getlist('skills')
    hackathon_id = request.GET.get('hackathon')

    # Get users seeking teams
    seeking_users = User.objects.filter(is_seeking_team=True)

    if filter_roles:
        seeking_users = seeking_users.filter(preferred_role__in=filter_roles)

    if filter_skills:
        # Filter users who have any of the selected skills in their skills JSON
        skill_q = Q()
        for skill in filter_skills:
            skill_q |= Q(skills__icontains=skill)
        seeking_users = seeking_users.filter(skill_q)

    # Get teams seeking members
    recruiting_teams = Team.objects.filter(
        is_seeking_members=True,
        status='forming'
    ).select_related('hackathon').prefetch_related(
        Prefetch('membership', queryset=TeamMember.objects.select_related('user'))
    ).annotate(
        members_count=Count('membership')
    )

    if hackathon_id:
        recruiting_teams = recruiting_teams.filter(hackathon_id=hackathon_id)

    # Get active hackathons for filter
    hackathons = HackathonPage.objects.filter(
        status__in=['upcoming', 'registration_open', 'in_progress']
    ).values('id', 'title')

    # Get available skills from users
    all_skills = set()
    for user in User.objects.exclude(skills=[]).values_list('skills', flat=True):
        if isinstance(user, list):
            all_skills.update(user)
    available_skills = sorted(all_skills)

    # Calculate stats
    stats = {
        'seeking_count': seeking_users.count(),
        'recruiting_count': recruiting_teams.count(),
    }

    # Build current user profile if authenticated
    current_user_profile = None
    if request.user.is_authenticated:
        current_user_profile = {
            'role': request.user.preferred_role,
            'skills': request.user.skills or [],
            'is_seeking': request.user.is_seeking_team,
        }

    # Build filters context
    filters = {
        'roles': filter_roles,
        'skills': filter_skills,
        'hackathon_id': int(hackathon_id) if hackathon_id else None,
    }

    # Add computed fields to users for template
    seeking_users_with_profile = []
    for user in seeking_users:
        user.role = user.preferred_role
        user.xp = user.xp_points
        user.reputation = float(user.reputation_score)
        user.profile_url = f'/users/{user.username}/'
        user.get_role_display = lambda u=user: dict(User._meta.get_field('preferred_role').choices).get(u.preferred_role, u.preferred_role)
        seeking_users_with_profile.append(user)

    # Add computed fields to teams for template
    recruiting_teams_with_data = []
    for team in recruiting_teams:
        team.members_count = team.members_count
        team.max_members = team.hackathon.max_team_size if hasattr(team.hackathon, 'max_team_size') else None
        # Determine needed roles based on hackathon requirements
        team.needed_roles = []
        if hasattr(team.hackathon, 'required_roles') and team.hackathon.required_roles:
            current_roles = set(team.membership.values_list('role', flat=True))
            team.needed_roles = [r for r in team.hackathon.required_roles if r not in current_roles]
        recruiting_teams_with_data.append(team)

    return render(request, 'pages/team_formation_page.html', {
        'seeking_users': seeking_users_with_profile,
        'recruiting_teams': recruiting_teams_with_data,
        'current_user_profile': current_user_profile,
        'filters': filters,
        'stats': stats,
        'hackathons': hackathons,
        'available_skills': available_skills,
    })


def quest_list(request):
    """Redirect to QuestIndexPage (Wagtail page)"""
    # Try to find a live page first
    index_page = QuestIndexPage.objects.live().first()
    # If no live page, try to find any page (for development/testing)
    if not index_page:
        index_page = QuestIndexPage.objects.first()

    if index_page:
        return redirect(index_page.url)
    # Fallback if no index page exists
    messages.info(request, 'Quests page not found. Please create a Quest Index Page in Wagtail admin.')
    return redirect('/')


def submission_list(request):
    """Redirect to SubmissionIndexPage (Wagtail page)"""
    # Try to find a live page first
    index_page = SubmissionIndexPage.objects.live().first()
    # If no live page, try to find any page (for development/testing)
    if not index_page:
        index_page = SubmissionIndexPage.objects.first()

    if index_page:
        return redirect(index_page.url)
    # Fallback if no index page exists
    messages.info(request, _('Submissions page not found. Please create a Submission Index Page in Wagtail admin.'))
    return redirect('/')


def quest_detail(request, slug):
    """
    Quest detail page view.

    Provides full context for quest detail template.
    """
    quest = get_object_or_404(Quest, slug=slug)

    # Get submissions for leaderboard
    submissions = Submission.objects.filter(
        quest=quest,
        verification_status='verified'
    ).select_related('user').order_by('-score', 'submitted_at')[:10]

    # Check if current user has submitted
    user_submission = None
    if request.user.is_authenticated:
        user_submission = Submission.objects.filter(
            user=request.user,
            quest=quest
        ).order_by('-submitted_at').first()

    # Calculate completion stats
    total_attempts = quest.submissions.count()
    completed = quest.submissions.filter(verification_status='verified').count()
    completion_rate = quest.get_completion_rate()

    context = {
        'quest': quest,
        'submissions': submissions,
        'user_submission': user_submission,
        'stats': {
            'total_attempts': total_attempts,
            'completed': completed,
            'completion_rate': completion_rate,
        },
        'related_quests': Quest.objects.filter(
            is_active=True,
            quest_type=quest.quest_type
        ).exclude(id=quest.id)[:3]
    }

    return render(request, 'pages/quest_detail_page.html', context)


@login_required
def create_team(request):
    """
    Redirect to community create_team view.
    Kept for backward compatibility with existing URLs.
    """
    return redirect('community:create_team')


@login_required
def join_team(request, slug):
    """
    Redirect to community join_team view.
    Kept for backward compatibility with existing URLs.
    """
    return redirect('community:join_team', slug=slug)


@login_required
def submit_quest(request, slug):
    """Submit a quest solution (placeholder view)"""
    quest = get_object_or_404(Quest, slug=slug)
    messages.info(request, _('Quest submission feature coming soon for %(title)s!') % {'title': quest.title})
    return redirect('/')


@login_required
def register_hackathon(request, slug):
    """
    Register a team for a hackathon.

    Creates a TeamRegistration linking the user's team to the hackathon.
    """
    hackathon = get_object_or_404(HackathonPage.objects.live(), slug=slug)

    # Get user's teams
    user_teams = TeamProfilePage.objects.live().filter(
        memberships__user=request.user
    ).distinct()

    if request.method == 'POST':
        team_id = request.POST.get('team_id')

        if not team_id:
            messages.error(request, _("Please select a team to register."))
            return redirect('hackathons:register_hackathon', slug=slug)

        team = get_object_or_404(TeamProfilePage.objects.live(), pk=team_id)

        # Verify user is a member of this team
        if not team.is_member(request.user):
            messages.error(request, _("You are not a member of this team."))
            return redirect('hackathons:register_hackathon', slug=slug)

        try:
            hackathon.register_team(team)
            messages.success(
                request,
                _("Team '%(team)s' has been registered for %(hackathon)s!") % {
                    'team': team.title,
                    'hackathon': hackathon.title
                }
            )
            return redirect(hackathon.url)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('hackathons:register_hackathon', slug=slug)

    # Check which teams are already registered
    registered_team_ids = hackathon.team_registrations.values_list('team_profile_id', flat=True)

    return render(request, 'hackathons/register_hackathon.html', {
        'hackathon': hackathon,
        'user_teams': user_teams,
        'registered_team_ids': list(registered_team_ids),
    })


@login_required
def submit_project(request, slug):
    """
    Submit a project to a hackathon.

    Creates a SubmissionPage under SubmissionIndexPage and associates it with the hackathon.
    Applies all configured validation rules from HackathonPage.
    """
    # Filter by current language to avoid MultipleObjectsReturned with translated pages
    hackathon = get_object_or_404(
        HackathonPage.objects.live().filter(locale__language_code=get_language()),
        slug=slug
    )

    # Get submission index page
    submission_index = SubmissionIndexPage.objects.live().first()
    if not submission_index:
        messages.error(
            request,
            _("Submission system is not configured. Please contact administrators.")
        )
        return redirect(hackathon.url)

    # Determine submission type based on hackathon configuration
    user_teams = None
    can_submit_individual = hackathon.submission_type in ('individual', 'both')
    can_submit_team = hackathon.submission_type in ('team', 'both')

    if can_submit_team:
        # Get user's registered teams for this hackathon
        user_teams = TeamProfilePage.objects.live().filter(
            memberships__user=request.user,
            hackathon_registrations__hackathon=hackathon,
            hackathon_registrations__status='approved'
        ).distinct()

    # Check if user can submit at all
    if hackathon.submission_type == 'team' and (not user_teams or not user_teams.exists()):
        messages.error(
            request,
            _("This hackathon requires team submissions. Please register a team first.")
        )
        return redirect('hackathons:register_hackathon', slug=slug)

    if request.method == 'POST':
        submission_mode = request.POST.get('submission_mode', 'individual')
        team_id = request.POST.get('team_id')
        project_title = request.POST.get('title', '').strip()
        tagline = request.POST.get('tagline', '').strip()

        if not project_title:
            messages.error(request, _("Project title is required."))
            return redirect('hackathons:submit_project', slug=slug)

        team = None
        submitter = None

        if submission_mode == 'team' and team_id:
            team = get_object_or_404(TeamProfilePage.objects.live(), pk=team_id)

            # Verify user is a member and team is registered
            if not team.is_member(request.user):
                messages.error(request, _("You are not a member of this team."))
                return redirect('hackathons:submit_project', slug=slug)

            if not hackathon.is_team_registered(team):
                messages.error(request, _("This team is not registered for the hackathon."))
                return redirect('hackathons:submit_project', slug=slug)

            # Check can_submit for team
            can_submit, reason = hackathon.can_submit(team_profile=team)
        else:
            # Individual submission
            submitter = request.user
            can_submit, reason = hackathon.can_submit(user=request.user)

        if not can_submit:
            messages.error(request, reason)
            return redirect('hackathons:submit_project', slug=slug)

        # Check for existing submission
        if team:
            existing = SubmissionPage.objects.live().filter(
                hackathons=hackathon,
                team_profile=team
            ).first()
        else:
            existing = SubmissionPage.objects.live().filter(
                hackathons=hackathon,
                submitter=submitter
            ).first()

        if existing and hackathon.max_submissions_per_participant == 1:
            if hackathon.allow_edit_after_submit:
                messages.warning(
                    request,
                    _("You already have a submission. Redirecting to edit page.")
                )
                return redirect(existing.url)
            else:
                messages.error(
                    request,
                    _("You already have a submission and editing is not allowed.")
                )
                return redirect(hackathon.url)

        # Generate slug
        project_slug = slugify(project_title)
        # Ensure unique slug
        base_slug = project_slug
        counter = 1
        while SubmissionPage.objects.filter(slug=project_slug).exists():
            project_slug = f"{base_slug}-{counter}"
            counter += 1

        # Create submission page under SubmissionIndexPage
        submission = SubmissionPage(
            title=project_title,
            slug=project_slug,
            team_profile=team,
            submitter=submitter,
            tagline=tagline,
        )

        # Add as child of submission index
        submission_index.add_child(instance=submission)

        # Associate with hackathon (M2M)
        submission.hackathons.add(hackathon)

        # Save and publish
        revision = submission.save_revision()
        revision.publish()

        messages.success(
            request,
            _("Project '%(title)s' submitted successfully!") % {'title': project_title}
        )
        return redirect(submission.url)

    # Check validation before showing form
    if can_submit_individual:
        can_submit_ind, reason_ind = hackathon.can_submit(user=request.user)
    else:
        can_submit_ind, reason_ind = False, _("Individual submissions not allowed")

    teams_with_status = []
    can_submit_team_any = False
    if can_submit_team and user_teams and user_teams.exists():
        # Check for at least one team that can submit
        for team in user_teams:
            can, reason = hackathon.can_submit(team_profile=team)
            teams_with_status.append({
                'team': team,
                'can_submit': can,
                'reason': reason,
            })
            if can:
                can_submit_team_any = True

    return render(request, 'hackathons/submit_project.html', {
        'hackathon': hackathon,
        'teams_with_status': teams_with_status,
        'can_submit_individual': can_submit_individual,
        'can_submit_team': can_submit_team,
        'can_submit_ind': can_submit_ind,
        'reason_ind': reason_ind,
        'can_submit_team_any': can_submit_team_any,
    })


# P2: Calendar API
@require_GET
def calendar_events_api(request):
    """
    Calendar API endpoint returning all hackathon phases as events.
    Returns JSON in format compatible with common calendar libraries (FullCalendar, etc.)

    Query parameters:
    - start: Filter events after this date (ISO format)
    - end: Filter events before this date (ISO format)
    - hackathon_id: Filter events for specific hackathon
    """
    # Parse query parameters
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    hackathon_id = request.GET.get('hackathon_id')

    # Base queryset
    phases = Phase.objects.select_related('hackathon').all()

    # Apply filters
    if start_date:
        phases = phases.filter(end_date__gte=start_date)
    if end_date:
        phases = phases.filter(start_date__lte=end_date)
    if hackathon_id:
        phases = phases.filter(hackathon_id=hackathon_id)

    # Convert to calendar events format
    events = []
    for phase in phases:
        events.append({
            'id': f'phase-{phase.id}',
            'title': f'{phase.hackathon.title}: {phase.title}',
            'start': phase.start_date.isoformat(),
            'end': phase.end_date.isoformat(),
            'description': phase.description,
            'url': phase.hackathon.url,
            'extendedProps': {
                'hackathon_id': phase.hackathon.id,
                'hackathon_title': phase.hackathon.title,
                'phase_id': phase.id,
                'phase_title': phase.title,
                'requirements': phase.requirements,
            }
        })

    return JsonResponse(events, safe=False)


@require_GET
def hackathon_timeline_api(request, hackathon_id):
    """
    Get detailed timeline for a specific hackathon.
    Includes phases, key dates, and current status.
    """
    try:
        hackathon = HackathonPage.objects.get(id=hackathon_id)
    except HackathonPage.DoesNotExist:
        return JsonResponse({'error': 'Hackathon not found'}, status=404)

    now = timezone.now()
    phases = hackathon.phases.all().order_by('start_date')

    timeline = {
        'hackathon': {
            'id': hackathon.id,
            'title': hackathon.title,
            'status': hackathon.status,
            'url': hackathon.url,
        },
        'current_phase': None,
        'phases': []
    }

    for phase in phases:
        phase_data = {
            'id': phase.id,
            'title': phase.title,
            'description': phase.description,
            'start_date': phase.start_date.isoformat(),
            'end_date': phase.end_date.isoformat(),
            'is_current': phase.start_date <= now <= phase.end_date,
            'is_past': phase.end_date < now,
            'is_future': phase.start_date > now,
            'requirements': phase.requirements,
        }
        timeline['phases'].append(phase_data)

        if phase_data['is_current']:
            timeline['current_phase'] = phase_data

    return JsonResponse(timeline)
