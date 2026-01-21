from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils import timezone

from .models import HackathonPage, Team, Quest, Phase


def team_list(request):
    """List all teams (placeholder view)"""
    teams = Team.objects.all()
    return render(request, 'hackathons/team_list.html', {
        'teams': teams,
    })


@login_required
def create_team(request):
    """Create a new team (placeholder view)"""
    messages.info(request, 'Team creation feature coming soon!')
    return redirect('/')


@login_required
def join_team(request, slug):
    """Join an existing team (placeholder view)"""
    team = get_object_or_404(Team, slug=slug)
    messages.info(request, f'Team joining feature coming soon for {team.name}!')
    return redirect('/')


@login_required
def submit_quest(request, slug):
    """Submit a quest solution (placeholder view)"""
    quest = get_object_or_404(Quest, slug=slug)
    messages.info(request, f'Quest submission feature coming soon for {quest.title}!')
    return redirect('/')


@login_required
def register_hackathon(request, slug):
    """Register for a hackathon (placeholder view)"""
    messages.info(request, 'Hackathon registration feature coming soon!')
    return redirect('/')


@login_required
def submit_project(request, slug):
    """Submit a hackathon project (placeholder view)"""
    messages.info(request, 'Project submission feature coming soon!')
    return redirect('/')


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
