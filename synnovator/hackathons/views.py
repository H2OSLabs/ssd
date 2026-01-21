from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import HackathonPage, Team, Quest


def hackathon_list(request):
    """List all hackathons (placeholder view)"""
    hackathons = HackathonPage.objects.live().public()
    return render(request, 'hackathons/hackathon_list.html', {
        'hackathons': hackathons,
    })


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
