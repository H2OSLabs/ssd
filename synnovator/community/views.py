"""
Community views for team management.

Implements team creation, joining, and management views.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from wagtail.models import Page

from .models import TeamIndexPage, TeamProfilePage, TeamMembership


def get_team_index_page():
    """Get the TeamIndexPage instance"""
    return TeamIndexPage.objects.live().first()


@login_required
def create_team(request):
    """
    Create a new team.

    Creates a TeamProfilePage under the TeamIndexPage
    and adds the creator as team leader.
    """
    team_index = get_team_index_page()
    if not team_index:
        messages.error(request, _("Team index page not found. Please contact administrator."))
        return redirect('/')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        tagline = request.POST.get('tagline', '').strip()
        role = request.POST.get('role', 'hacker')

        if not name:
            messages.error(request, _("Team name is required."))
            return render(request, 'community/create_team.html')

        # Generate slug
        slug = slugify(name)

        # Check if slug already exists
        if TeamProfilePage.objects.filter(slug=slug).exists():
            messages.error(request, _("A team with this name already exists."))
            return render(request, 'community/create_team.html')

        # Create the team page
        team_page = TeamProfilePage(
            title=name,
            slug=slug,
            tagline=tagline,
        )

        # Add as child of team index
        team_index.add_child(instance=team_page)

        # Publish the page
        revision = team_page.save_revision()
        revision.publish()

        # Refresh from DB to get the django_group created in save()
        team_page.refresh_from_db()

        # Add creator as leader
        team_page.add_member(request.user, role=role, is_leader=True)

        messages.success(request, _("Team '%(name)s' created successfully!") % {'name': name})
        return redirect(team_page.url)

    return render(request, 'community/create_team.html')


@login_required
def join_team(request, slug):
    """
    Join a team.

    Adds the user as a member of the team.
    """
    team_page = get_object_or_404(TeamProfilePage.objects.live(), slug=slug)

    if request.method == 'POST':
        role = request.POST.get('role', 'member')

        try:
            team_page.add_member(request.user, role=role)
            messages.success(request, _("You have joined team '%(name)s'!") % {'name': team_page.title})
        except ValueError as e:
            messages.error(request, str(e))

        return redirect(team_page.url)

    return render(request, 'community/join_team.html', {'team': team_page})


@login_required
def leave_team(request, slug):
    """
    Leave a team.

    Removes the user from the team.
    """
    team_page = get_object_or_404(TeamProfilePage.objects.live(), slug=slug)

    if request.method == 'POST':
        try:
            team_page.remove_member(request.user)
            messages.success(request, _("You have left team '%(name)s'.") % {'name': team_page.title})
        except ValueError as e:
            messages.error(request, str(e))

        return redirect('/')

    return render(request, 'community/leave_team.html', {'team': team_page})


@login_required
@require_POST
def remove_member(request, slug, user_id):
    """
    Remove a member from the team.

    Only team leader can remove members.
    """
    team_page = get_object_or_404(TeamProfilePage.objects.live(), slug=slug)

    # Check if current user is leader
    leader_membership = team_page.memberships.filter(user=request.user, is_leader=True).first()
    if not leader_membership and not request.user.is_superuser:
        messages.error(request, _("Only team leaders can remove members."))
        return redirect(team_page.url)

    from django.contrib.auth import get_user_model
    User = get_user_model()
    user_to_remove = get_object_or_404(User, pk=user_id)

    try:
        team_page.remove_member(user_to_remove)
        messages.success(request, _("Member removed from team."))
    except ValueError as e:
        messages.error(request, str(e))

    return redirect(team_page.url)


def team_list(request):
    """
    List all teams that are open for new members.
    """
    teams = TeamProfilePage.objects.live().filter(is_open_for_members=True)

    # Apply filters if provided
    role_filter = request.GET.get('seeking_role')
    if role_filter:
        # Filter teams that don't have this role filled to max
        teams = teams.filter(is_open_for_members=True)

    return render(request, 'community/team_list.html', {
        'teams': teams,
    })


def team_detail(request, slug):
    """
    View team details.
    """
    team_page = get_object_or_404(TeamProfilePage.objects.live(), slug=slug)

    is_member = False
    is_leader = False
    user_membership = None

    if request.user.is_authenticated:
        user_membership = team_page.memberships.filter(user=request.user).first()
        if user_membership:
            is_member = True
            is_leader = user_membership.is_leader

    return render(request, 'community/team_detail.html', {
        'team': team_page,
        'is_member': is_member,
        'is_leader': is_leader,
        'user_membership': user_membership,
    })
