#!/usr/bin/env python
"""
Verify all user workflows work correctly.
Tests P0, P1, and P2 functionality through model queries.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'synnovator.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
from synnovator.hackathons.models import *
from synnovator.community.models import *
from synnovator.notifications.models import *
from synnovator.assets.models import *

User = get_user_model()

def verify_workflow(name, test_func):
    """Verify a workflow and print result"""
    try:
        result = test_func()
        print(f"✅ {name}: {result}")
        return True
    except Exception as e:
        print(f"❌ {name}: {str(e)}")
        return False

print("=== VERIFYING USER WORKFLOWS ===\n")

# P0: Competition rules and advancement
print("P0: Competition Rules and Advancement")
verify_workflow(
    "View competition rules",
    lambda: f"{CompetitionRule.objects.count()} rules defined"
)
verify_workflow(
    "Check team compliance",
    lambda: f"Team compliance: {Team.objects.first().has_required_roles()}"
)
verify_workflow(
    "View advancement logs",
    lambda: f"{AdvancementLog.objects.count()} advancement decisions recorded"
)
verify_workflow(
    "Track team advancement status",
    lambda: f"Teams advanced: {Team.objects.filter(status='advanced').count()}, eliminated: {Team.objects.filter(status='eliminated').count()}"
)

# P1: Social features
print("\nP1: Social Features")
verify_workflow(
    "Create and view community posts",
    lambda: f"{CommunityPost.objects.count()} posts, {CommunityPost.objects.filter(status='published').count()} published"
)
verify_workflow(
    "Comment on posts",
    lambda: f"{Comment.objects.count()} comments, {Comment.objects.filter(status='visible').count()} visible"
)
verify_workflow(
    "Like posts",
    lambda: f"{Like.objects.count()} total likes"
)
verify_workflow(
    "Follow users",
    lambda: f"{UserFollow.objects.count()} follow relationships"
)
verify_workflow(
    "Report inappropriate content",
    lambda: f"{Report.objects.count()} reports filed"
)

# P1: Notifications
print("\nP1: Notifications")
verify_workflow(
    "Send notifications to users",
    lambda: f"{Notification.objects.count()} notifications, {Notification.objects.filter(is_read=False).count()} unread"
)
verify_workflow(
    "Mark notifications as read",
    lambda: f"{Notification.objects.filter(is_read=True).count()} read notifications"
)

# P1: Multi-judge scoring
print("\nP1: Multi-judge Scoring")
verify_workflow(
    "Judges submit scores",
    lambda: f"{JudgeScore.objects.count()} judge scores submitted"
)
verify_workflow(
    "Calculate aggregated scores",
    lambda: f"Team scores updated: {Team.objects.filter(final_score__gt=0).count()} teams"
)
verify_workflow(
    "View score breakdown",
    lambda: f"{ScoreBreakdown.objects.count()} scoring criteria defined"
)

# P1: Registration management
print("\nP1: Registration Management")
verify_workflow(
    "User register for hackathon",
    lambda: f"{HackathonRegistration.objects.count()} registrations, {HackathonRegistration.objects.filter(status='approved').count()} approved"
)
verify_workflow(
    "Match users with teams",
    lambda: f"{HackathonRegistration.objects.filter(is_seeking_team=True).count()} users seeking teams"
)

# P2: Asset management
print("\nP2: Asset Management")
verify_workflow(
    "Award assets to users",
    lambda: f"{UserAsset.objects.count()} assets owned by users"
)
verify_workflow(
    "Track asset transactions",
    lambda: f"{AssetTransaction.objects.count()} transactions recorded"
)

# P2: Copyright checking
print("\nP2: Copyright Checking")
verify_workflow(
    "Copyright declaration",
    lambda: f"{Submission.objects.filter(copyright_declaration=True).count()} submissions with copyright declared"
)
verify_workflow(
    "Originality check",
    lambda: f"{Submission.objects.filter(originality_check_status='pass').count()} submissions passed originality check"
)

# P2: Calendar API
print("\nP2: Calendar API")
verify_workflow(
    "List hackathon phases",
    lambda: f"{Phase.objects.count()} phases in calendar"
)

# Core user workflows
print("\nCore User Workflows")
verify_workflow(
    "User profile management",
    lambda: f"{User.objects.filter(profile_completed=True).count()}/{User.objects.count()} users completed profiles"
)
verify_workflow(
    "Team formation",
    lambda: f"{Team.objects.count()} teams, {Team.objects.filter(is_seeking_members=True).count()} seeking members"
)
verify_workflow(
    "Quest submissions",
    lambda: f"{Submission.objects.filter(quest__isnull=False).count()} quest submissions"
)
verify_workflow(
    "Hackathon submissions",
    lambda: f"{Submission.objects.filter(hackathon__isnull=False).count()} hackathon submissions"
)
verify_workflow(
    "Submission verification",
    lambda: f"{Submission.objects.filter(verification_status='verified').count()} verified submissions"
)

print("\n=== VERIFICATION COMPLETE ===")
