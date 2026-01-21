"""
Management command to create comprehensive mock data for testing all features.
Tests P0, P1, and P2 functionality.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from synnovator.hackathons.models import (
    HackathonPage, Phase, Prize, Team, TeamMember, Quest, Submission,
    CompetitionRule, RuleViolation, AdvancementLog,
    JudgeScore, ScoreBreakdown, HackathonRegistration
)
from synnovator.community.models import CommunityPost, Comment, Like, UserFollow, Report
from synnovator.notifications.models import Notification
from synnovator.assets.models import UserAsset, AssetTransaction
from synnovator.home.models import HomePage

User = get_user_model()


class Command(BaseCommand):
    help = 'Create comprehensive mock data for testing P0+P1+P2 features'

    def handle(self, *args, **options):
        self.stdout.write('Creating mock data...\n')

        # Create users
        self.stdout.write('Creating users...')
        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            admin = User.objects.create_superuser('admin', 'admin@example.com', 'password')

        users = []
        for i in range(10):
            user, created = User.objects.get_or_create(
                username=f'user{i}',
                defaults={
                    'email': f'user{i}@example.com',
                    'first_name': f'User',
                    'last_name': f'{i}',
                    'preferred_role': ['hacker', 'hipster', 'hustler'][i % 3],
                    'bio': f'Test user {i} bio',
                    'skills': ['Python', 'Django', 'React'][0:i%3+1],
                    'xp_points': i * 100,
                    'level': (i * 100) // 100 + 1,
                    'profile_completed': True,
                    'is_seeking_team': i % 2 == 0,
                }
            )
            if created:
                user.set_password('password')
                user.save()
            users.append(user)
        self.stdout.write(self.style.SUCCESS(f'Created {len(users)} users'))

        # Get or create home page
        self.stdout.write('Getting home page...')
        home_page = HomePage.objects.first()
        if not home_page:
            self.stdout.write(self.style.ERROR('No home page found. Run wagtail site initialization first.'))
            return

        # Create hackathon
        self.stdout.write('Creating hackathon...')
        hackathon = HackathonPage.objects.filter(slug='ai-innovation-2026').first()
        
        if not hackathon:
            hackathon = HackathonPage(
                title='AI Innovation Challenge 2026',
                slug='ai-innovation-2026',
                description='<p>Build the future of AI technology</p>',
                min_team_size=2,
                max_team_size=5,
                allow_solo=False,
                required_roles=['hacker', 'hustler'],
                passing_score=80.0,
                status='in_progress',
            )
            home_page.add_child(instance=hackathon)
            hackathon.save_revision().publish()
        
        self.stdout.write(self.style.SUCCESS('Created hackathon'))

        # Create phases
        self.stdout.write('Creating phases...')
        now = timezone.now()
        phases_data = [
            ('Registration', now - timedelta(days=30), now - timedelta(days=20)),
            ('Team Formation', now - timedelta(days=20), now - timedelta(days=15)),
            ('Hacking Period', now - timedelta(days=15), now + timedelta(days=5)),
            ('Judging', now + timedelta(days=5), now + timedelta(days=10)),
            ('Awards', now + timedelta(days=10), now + timedelta(days=11)),
        ]
        
        for i, (title, start, end) in enumerate(phases_data):
            Phase.objects.get_or_create(
                hackathon=hackathon,
                title=title,
                defaults={
                    'description': f'{title} phase',
                    'start_date': start,
                    'end_date': end,
                    'order': i,
                    'requirements': {'min_progress': 50 if i > 2 else 0}
                }
            )
        self.stdout.write(self.style.SUCCESS('Created 5 phases'))

        # Create prizes
        self.stdout.write('Creating prizes...')
        prizes_data = [
            ('First Place', 1, 10000),
            ('Second Place', 2, 5000),
            ('Third Place', 3, 2500),
        ]
        
        for title, rank, value in prizes_data:
            Prize.objects.get_or_create(
                hackathon=hackathon,
                rank=rank,
                defaults={
                    'title': title,
                    'monetary_value': value,
                    'description': f'{title} prize',
                    'benefits': ['Trophy', 'Certificate', 'Cloud Credits']
                }
            )
        self.stdout.write(self.style.SUCCESS('Created 3 prizes'))

        # Create competition rules
        self.stdout.write('Creating competition rules...')
        CompetitionRule.objects.get_or_create(
            hackathon=hackathon,
            title='Team Size Rule',
            defaults={
                'rule_type': 'team_size',
                'description': 'Teams must have 2-5 members',
                'rule_definition': {'min_members': 2, 'max_members': 5},
                'is_mandatory': True,
                'penalty': 'disqualification',
                'order': 1,
            }
        )
        
        CompetitionRule.objects.get_or_create(
            hackathon=hackathon,
            title='Required Roles',
            defaults={
                'rule_type': 'team_composition',
                'description': 'Must have hacker and hustler',
                'rule_definition': {'required_roles': ['hacker', 'hustler']},
                'is_mandatory': True,
                'penalty': 'disqualification',
                'order': 2,
            }
        )
        self.stdout.write(self.style.SUCCESS('Created 2 competition rules'))

        # Create teams
        self.stdout.write('Creating teams...')
        teams = []
        for i in range(3):
            team, created = Team.objects.get_or_create(
                hackathon=hackathon,
                slug=f'team-{i}',
                defaults={
                    'name': f'Team {i}',
                    'tagline': f'Building awesome project {i}',
                    'status': ['ready', 'submitted', 'verified'][i],
                    'final_score': (i + 1) * 25.0,
                    'technical_score': (i + 1) * 30.0,
                    'commercial_score': (i + 1) * 25.0,
                    'operational_score': (i + 1) * 20.0,
                    'is_seeking_members': i == 0,
                    'current_round': 1,
                }
            )
            teams.append(team)
            
            # Add team members
            if created:
                for j in range(min(3, len(users) - i*3)):
                    user_idx = i * 3 + j
                    if user_idx < len(users):
                        TeamMember.objects.get_or_create(
                            team=team,
                            user=users[user_idx],
                            defaults={
                                'role': ['hacker', 'hipster', 'hustler'][j % 3],
                                'is_leader': j == 0,
                            }
                        )
        self.stdout.write(self.style.SUCCESS(f'Created {len(teams)} teams with members'))

        # Create quests
        self.stdout.write('Creating quests...')
        quests = []
        for i in range(5):
            quest, created = Quest.objects.get_or_create(
                slug=f'quest-{i}',
                defaults={
                    'title': f'Quest {i}: {"Technical" if i < 2 else "Commercial" if i < 4 else "Operational"} Challenge',
                    'description': f'<p>Complete this {i+1}-level challenge</p>',
                    'quest_type': ['technical', 'technical', 'commercial', 'commercial', 'operational'][i],
                    'difficulty': ['beginner', 'intermediate', 'advanced', 'advanced', 'expert'][i],
                    'xp_reward': (i + 1) * 50,
                    'estimated_time_minutes': (i + 1) * 60,
                    'hackathon': hackathon if i < 3 else None,
                    'is_active': True,
                    'tags': ['python', 'ml', 'api'][0:i%3+1],
                }
            )
            quests.append(quest)
        self.stdout.write(self.style.SUCCESS('Created 5 quests'))

        # Create submissions
        self.stdout.write('Creating submissions...')
        for i, team in enumerate(teams):
            Submission.objects.get_or_create(
                team=team,
                hackathon=hackathon,
                defaults={
                    'submission_url': f'https://github.com/team{i}/project',
                    'description': f'Our amazing project for Team {i}',
                    'verification_status': ['verified', 'verified', 'pending'][i],
                    'score': (i + 1) * 25.0,
                    'feedback': f'Good work from Team {i}',
                    'verified_by': admin if i < 2 else None,
                    'verified_at': now if i < 2 else None,
                    'copyright_declaration': True,
                    'originality_check_status': 'pass',
                    'file_transfer_confirmed': True,
                }
            )
        
        # Create individual quest submissions
        for i in range(3):
            Submission.objects.get_or_create(
                user=users[i],
                quest=quests[i],
                defaults={
                    'submission_url': f'https://github.com/user{i}/quest-{i}',
                    'description': f'Quest solution by user {i}',
                    'verification_status': 'verified',
                    'score': 85.0 + i * 5,
                    'verified_by': admin,
                    'verified_at': now,
                    'copyright_declaration': True,
                    'originality_check_status': 'pass',
                }
            )
        self.stdout.write(self.style.SUCCESS('Created submissions'))

        # Create judge scores
        self.stdout.write('Creating judge scores...')
        judges = users[:3]  # First 3 users are judges
        for team in teams:
            for submission in team.submissions.filter(verification_status='verified'):
                for judge in judges:
                    JudgeScore.objects.get_or_create(
                        submission=submission,
                        judge=judge,
                        defaults={
                            'technical_score': 75.0 + team.id * 5,
                            'commercial_score': 70.0 + team.id * 5,
                            'operational_score': 65.0 + team.id * 5,
                            'feedback': f'Good work from judge {judge.username}',
                        }
                    )
        self.stdout.write(self.style.SUCCESS('Created judge scores'))

        # Create hackathon registrations
        self.stdout.write('Creating registrations...')
        for i, user in enumerate(users):
            HackathonRegistration.objects.get_or_create(
                hackathon=hackathon,
                user=user,
                defaults={
                    'status': 'approved',
                    'preferred_role': user.preferred_role,
                    'is_seeking_team': i % 2 == 0,
                    'motivation': f'I want to build great things! - {user.username}',
                    'skills': user.skills,
                    'team': teams[i // 3] if i < 9 else None,
                }
            )
        self.stdout.write(self.style.SUCCESS('Created registrations'))

        # Create community posts
        self.stdout.write('Creating community posts...')
        for i in range(5):
            post, created = CommunityPost.objects.get_or_create(
                author=users[i],
                title=f'Post {i}: Looking for team members',
                defaults={
                    'content': f'<p>Hi everyone! I\'m looking for {["hacker", "hipster", "hustler"][i%3]} teammates.</p>',
                    'status': 'published',
                    'hackathon': hackathon if i < 3 else None,
                }
            )
            
            # Add comments
            if created:
                for j in range(2):
                    Comment.objects.create(
                        post=post,
                        author=users[(i+j+1) % len(users)],
                        content=f'Great post! I\'m interested - comment {j}',
                        status='visible',
                    )
                
                # Add likes
                for j in range(3):
                    Like.objects.get_or_create(
                        user=users[(i+j) % len(users)],
                        post=post,
                    )
        self.stdout.write(self.style.SUCCESS('Created community posts with comments and likes'))

        # Create user follows
        self.stdout.write('Creating user follows...')
        for i in range(5):
            for j in range(i+1, min(i+3, len(users))):
                UserFollow.objects.get_or_create(
                    follower=users[i],
                    following=users[j],
                )
        self.stdout.write(self.style.SUCCESS('Created user follows'))

        # Create notifications
        self.stdout.write('Creating notifications...')
        for i, user in enumerate(users[:5]):
            Notification.objects.get_or_create(
                recipient=user,
                notification_type=['advancement_result', 'submission_reviewed', 'team_invitation', 'post_liked', 'new_follower'][i],
                defaults={
                    'title': f'Notification {i} for {user.username}',
                    'message': f'This is test notification {i}',
                    'is_read': i % 2 == 0,
                }
            )
        self.stdout.write(self.style.SUCCESS('Created notifications'))

        # Create user assets
        self.stdout.write('Creating user assets...')
        for i, user in enumerate(users[:5]):
            AssetTransaction.award_asset(
                user=user,
                asset_type='badge',
                asset_id=f'first_submission_badge',
                quantity=1,
                reason='Completed first submission',
            )
            
            AssetTransaction.award_asset(
                user=user,
                asset_type='coin',
                asset_id='hackathon_coin',
                quantity=(i + 1) * 10,
                reason='Participation reward',
            )
        self.stdout.write(self.style.SUCCESS('Created user assets and transactions'))

        # Create advancement logs
        self.stdout.write('Creating advancement logs...')
        AdvancementLog.objects.get_or_create(
            team=teams[0],
            defaults={
                'decision': 'advanced',
                'decided_by': admin,
                'notes': 'Excellent performance, advancing to next round',
            }
        )
        
        AdvancementLog.objects.get_or_create(
            team=teams[2],
            defaults={
                'decision': 'eliminated',
                'decided_by': admin,
                'notes': 'Did not meet minimum requirements',
            }
        )
        self.stdout.write(self.style.SUCCESS('Created advancement logs'))

        self.stdout.write(self.style.SUCCESS('\n✅ Mock data creation completed successfully!'))
        self.stdout.write('\nSummary:')
        self.stdout.write(f'  Users: {User.objects.count()}')
        self.stdout.write(f'  Hackathons: {HackathonPage.objects.count()}')
        self.stdout.write(f'  Teams: {Team.objects.count()}')
        self.stdout.write(f'  Quests: {Quest.objects.count()}')
        self.stdout.write(f'  Submissions: {Submission.objects.count()}')
        self.stdout.write(f'  Community Posts: {CommunityPost.objects.count()}')
        self.stdout.write(f'  Comments: {Comment.objects.count()}')
        self.stdout.write(f'  Likes: {Like.objects.count()}')
        self.stdout.write(f'  Notifications: {Notification.objects.count()}')
        self.stdout.write(f'  User Assets: {UserAsset.objects.count()}')
        self.stdout.write(f'  Registrations: {HackathonRegistration.objects.count()}')
