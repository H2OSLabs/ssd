"""
Pytest fixtures for hackathons app tests.
"""

import pytest
from synnovator.hackathons.tests.factories import (
    HackathonIndexPageFactory,
    HackathonPageFactory,
    QuestFactory,
    TeamFactory,
    TeamMemberFactory,
    PhaseFactory,
    PrizeFactory,
    SubmissionFactory,
)
from synnovator.users.tests.factories import UserFactory


@pytest.fixture
def hackathon_index(db, wagtail_root):
    """Create a HackathonIndexPage."""
    return HackathonIndexPageFactory(parent=wagtail_root)


@pytest.fixture
def hackathon(db, hackathon_index):
    """Create a HackathonPage."""
    return HackathonPageFactory(parent=hackathon_index)


@pytest.fixture
def quest(db):
    """Create a Quest."""
    return QuestFactory()


@pytest.fixture
def team(db, hackathon):
    """Create a Team for hackathon."""
    return TeamFactory(hackathon=hackathon)


@pytest.fixture
def team_with_members(db, hackathon):
    """Create a Team with members."""
    team = TeamFactory(hackathon=hackathon)
    leader = UserFactory()
    member1 = UserFactory()
    member2 = UserFactory()

    TeamMemberFactory(team=team, user=leader, is_leader=True, role="hustler")
    TeamMemberFactory(team=team, user=member1, is_leader=False, role="hacker")
    TeamMemberFactory(team=team, user=member2, is_leader=False, role="hipster")

    return team


@pytest.fixture
def phase(db, hackathon):
    """Create a Phase for hackathon."""
    return PhaseFactory(hackathon=hackathon)


@pytest.fixture
def prize(db, hackathon):
    """Create a Prize for hackathon."""
    return PrizeFactory(hackathon=hackathon)


@pytest.fixture
def submission(db, quest):
    """Create a Submission for a quest."""
    user = UserFactory()
    return SubmissionFactory(user=user, quest=quest)
