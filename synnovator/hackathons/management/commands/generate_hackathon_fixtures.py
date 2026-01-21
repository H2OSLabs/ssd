"""
Management command to generate realistic mock data for hackathon platform testing.

Generates:
- Users (20-30): Varied XP, roles, skills, bios
- Hackathons (5): Different statuses
- Phases (4-6 per hackathon): Registration → Hacking → Judging → Awards
- Teams (30-40): Mix of statuses
- TeamMembers (80-120): Proper role distribution
- Quests (25-35): All difficulty levels
- Submissions (100-150): Mix of verification statuses
- Prizes (3-5 per hackathon): Monetary + benefits
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from faker import Faker

from wagtail.models import Page
from synnovator.hackathons.models import (
    HackathonPage, Phase, Prize, Team, TeamMember, Quest, Submission
)

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Generate realistic mock data for hackathon platform'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing hackathon data before generating new data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing hackathon data...')
            self.clear_data()

        self.stdout.write('Generating mock data...')

        # Generate data in order of dependencies
        users = self.generate_users()
        self.stdout.write(self.style.SUCCESS(f'✓ Generated {len(users)} users'))

        hackathons = self.generate_hackathons()
        self.stdout.write(self.style.SUCCESS(f'✓ Generated {len(hackathons)} hackathons'))

        # Phases and prizes are created inline with hackathons
        total_phases = sum(h.phases.count() for h in hackathons)
        total_prizes = sum(h.prizes.count() for h in hackathons)
        self.stdout.write(self.style.SUCCESS(f'✓ Generated {total_phases} phases'))
        self.stdout.write(self.style.SUCCESS(f'✓ Generated {total_prizes} prizes'))

        quests = self.generate_quests(hackathons)
        self.stdout.write(self.style.SUCCESS(f'✓ Generated {len(quests)} quests'))

        teams = self.generate_teams(hackathons, users)
        self.stdout.write(self.style.SUCCESS(f'✓ Generated {len(teams)} teams'))

        team_members = self.generate_team_members(teams, users)
        self.stdout.write(self.style.SUCCESS(f'✓ Generated {len(team_members)} team members'))

        submissions = self.generate_submissions(users, teams, quests, hackathons)
        self.stdout.write(self.style.SUCCESS(f'✓ Generated {len(submissions)} submissions'))

        self.stdout.write(self.style.SUCCESS('\n✅ Mock data generation complete!'))

    def clear_data(self):
        """Clear all hackathon-related data."""
        Submission.objects.all().delete()
        TeamMember.objects.all().delete()
        Team.objects.all().delete()
        Quest.objects.all().delete()
        HackathonPage.objects.all().delete()
        # Clear users except superusers
        User.objects.filter(is_superuser=False).delete()

    def generate_users(self):
        """Generate 20-30 users with varied profiles."""
        users = []
        num_users = random.randint(20, 30)

        roles = ['hacker', 'hipster', 'hustler', 'mentor', 'any']
        skill_pools = {
            'hacker': ['Python', 'JavaScript', 'React', 'Django', 'ML', 'DevOps', 'Go', 'Rust', 'AWS'],
            'hipster': ['UI/UX', 'Figma', 'Adobe XD', 'Design Thinking', 'User Research', 'Prototyping'],
            'hustler': ['Marketing', 'Sales', 'Business Strategy', 'Product Management', 'Analytics', 'Pitch Deck'],
            'mentor': ['Leadership', 'Coaching', 'Startup Experience', 'Technical Architecture'],
            'any': ['Agile', 'Communication', 'Problem Solving', 'Team Building']
        }

        for i in range(num_users):
            role = random.choice(roles)
            first_name = fake.first_name()
            last_name = fake.last_name()
            username = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}"

            # Varied XP distribution
            xp = random.choices(
                [random.randint(0, 500), random.randint(500, 2000), random.randint(2000, 5000)],
                weights=[0.5, 0.3, 0.2]
            )[0]

            # Select skills based on role
            all_skills = skill_pools.get(role, skill_pools['any'])
            skills = random.sample(all_skills, k=random.randint(2, min(5, len(all_skills))))

            user = User.objects.create_user(
                username=username,
                email=f"{username}@example.com",
                first_name=first_name,
                last_name=last_name,
                password='password123',
                preferred_role=role,
                bio=fake.text(max_nb_chars=200),
                skills=skills,
                xp_points=xp,
                level=(xp // 100) + 1,
                reputation_score=Decimal(str(random.uniform(0, 100))),
                profile_completed=random.choice([True, True, False]),  # Most completed
                is_seeking_team=random.choice([True, False]),
            )
            users.append(user)

        return users

    def generate_hackathons(self):
        """Generate 5 hackathons with different statuses."""
        hackathons = []

        # Get home page as parent
        home_page = Page.objects.filter(depth=2).first()
        if not home_page:
            self.stdout.write(self.style.ERROR('No home page found. Please create one first.'))
            return hackathons

        statuses = ['upcoming', 'registration_open', 'in_progress', 'judging', 'completed']
        hackathon_themes = [
            ('AI Innovation Challenge', 'Build the next generation of AI-powered solutions'),
            ('FinTech Revolution', 'Reimagine financial services with technology'),
            ('HealthTech Hackathon', 'Create innovative healthcare solutions'),
            ('Sustainability Sprint', 'Develop tech solutions for environmental challenges'),
            ('Web3 Builder Fest', 'Build decentralized applications and smart contracts'),
        ]

        for idx, (title, description) in enumerate(hackathon_themes):
            status = statuses[idx]

            hackathon = HackathonPage(
                title=title,
                description=f"<p>{description}</p>",
                min_team_size=random.randint(2, 3),
                max_team_size=random.randint(4, 6),
                allow_solo=random.choice([True, False]),
                required_roles=['hacker'] if random.random() > 0.5 else [],
                passing_score=Decimal(str(random.randint(70, 85))),
                status=status,
                slug=slugify(title),
            )

            # Add to home page
            home_page.add_child(instance=hackathon)
            hackathon.save_revision().publish()

            # Generate phases for this hackathon
            self.generate_phases(hackathon, status)

            # Generate prizes for this hackathon
            self.generate_prizes(hackathon)

            hackathons.append(hackathon)

        return hackathons

    def generate_phases(self, hackathon, status):
        """Generate 4-6 phases for a hackathon based on its status."""
        base_date = timezone.now()

        # Adjust base date based on status
        if status == 'completed':
            base_date = base_date - timedelta(days=60)
        elif status == 'judging':
            base_date = base_date - timedelta(days=30)
        elif status == 'in_progress':
            base_date = base_date - timedelta(days=15)
        elif status == 'registration_open':
            base_date = base_date - timedelta(days=5)
        else:  # upcoming
            base_date = base_date + timedelta(days=10)

        phase_templates = [
            ('Registration', 'Sign up and complete your profile', 7),
            ('Team Formation', 'Find teammates and form your team', 5),
            ('Ideation & Planning', 'Brainstorm and plan your project', 3),
            ('Hacking Period', 'Build your solution', 14),
            ('Submission Deadline', 'Submit your final project', 2),
            ('Judging', 'Judges review and score submissions', 5),
            ('Awards Ceremony', 'Winners announced and prizes awarded', 1),
        ]

        # Select 4-6 phases
        num_phases = random.randint(4, 6)
        selected_phases = random.sample(phase_templates, k=min(num_phases, len(phase_templates)))

        current_date = base_date
        for order, (title, description, duration) in enumerate(selected_phases):
            start_date = current_date
            end_date = current_date + timedelta(days=duration)

            Phase.objects.create(
                hackathon=hackathon,
                title=title,
                description=description,
                start_date=start_date,
                end_date=end_date,
                order=order,
            )

            current_date = end_date

    def generate_prizes(self, hackathon):
        """Generate 3-5 prizes per hackathon."""
        num_prizes = random.randint(3, 5)

        prize_templates = [
            ('First Place', 'Grand prize winner', 1, [10000, 15000], ['Incubation program access', 'Mentorship by industry leaders']),
            ('Second Place', 'Runner-up prize', 2, [5000, 7500], ['AWS credits', 'Tech toolkit']),
            ('Third Place', 'Bronze medal', 3, [2500, 5000], ['Online course subscriptions', 'Networking event access']),
            ('Best AI Solution', 'Most innovative use of AI', 4, [3000, 5000], ['OpenAI API credits', 'ML toolkit']),
            ('Best Design', 'Outstanding user experience', 5, [2000, 3000], ['Design software licenses', 'UX masterclass']),
            ('People\'s Choice', 'Community favorite', 6, [1000, 2000], ['Swag pack', 'Social media promotion']),
        ]

        selected_prizes = random.sample(prize_templates, k=min(num_prizes, len(prize_templates)))

        for title, description, rank, monetary_range, benefits in selected_prizes:
            Prize.objects.create(
                hackathon=hackathon,
                title=title,
                description=description,
                rank=rank,
                monetary_value=Decimal(str(random.randint(*monetary_range))),
                benefits=random.sample(benefits, k=random.randint(1, len(benefits))),
            )

    def generate_quests(self, hackathons):
        """Generate 25-35 quests across different difficulties and types."""
        quests = []
        num_quests = random.randint(25, 35)

        quest_types = ['technical', 'commercial', 'operational', 'mixed']
        difficulties = ['beginner', 'intermediate', 'advanced', 'expert']

        quest_templates = {
            'technical': [
                'Build a REST API', 'Create a React Dashboard', 'Implement OAuth Authentication',
                'Set up CI/CD Pipeline', 'Deploy with Docker', 'Build ML Model',
                'Create Microservice', 'Optimize Database Queries', 'Write Unit Tests'
            ],
            'commercial': [
                'Create Business Model Canvas', 'Develop Marketing Strategy', 'Write Pitch Deck',
                'Conduct User Research', 'Analyze Competitor Landscape', 'Define Value Proposition'
            ],
            'operational': [
                'Design User Flow', 'Create Wireframes', 'Conduct Usability Testing',
                'Build Design System', 'Create Prototype', 'Map Customer Journey'
            ],
            'mixed': [
                'Launch MVP', 'Complete Product Roadmap', 'Create Go-to-Market Plan',
                'Build Full-Stack Feature', 'Conduct A/B Testing'
            ]
        }

        skill_tags = {
            'technical': ['python', 'javascript', 'docker', 'kubernetes', 'aws', 'react', 'django', 'api', 'ml'],
            'commercial': ['marketing', 'sales', 'strategy', 'analytics', 'growth', 'product'],
            'operational': ['design', 'ux', 'ui', 'figma', 'prototyping', 'user-research'],
            'mixed': ['full-stack', 'mvp', 'product-management', 'agile']
        }

        for i in range(num_quests):
            quest_type = random.choice(quest_types)
            difficulty = random.choice(difficulties)

            # Get template based on type
            templates = quest_templates[quest_type]
            title = f"{random.choice(templates)} - {fake.catch_phrase()}"

            # XP based on difficulty
            xp_map = {'beginner': 50, 'intermediate': 100, 'advanced': 200, 'expert': 350}
            time_map = {'beginner': 30, 'intermediate': 60, 'advanced': 120, 'expert': 240}

            # 30% chance to be hackathon-specific
            hackathon = random.choice(hackathons) if random.random() < 0.3 else None

            tags = random.sample(skill_tags[quest_type], k=random.randint(2, 4))

            quest = Quest.objects.create(
                title=title[:200],  # Truncate if needed
                slug=slugify(f"{title}-{i}"),
                description=f"<p>{fake.paragraph(nb_sentences=3)}</p>",
                quest_type=quest_type,
                difficulty=difficulty,
                xp_reward=xp_map[difficulty],
                estimated_time_minutes=time_map[difficulty],
                hackathon=hackathon,
                is_active=random.choice([True, True, True, False]),  # 75% active
                tags=tags,
            )
            quests.append(quest)

        return quests

    def generate_teams(self, hackathons, users):
        """Generate 30-40 teams with varied statuses."""
        teams = []
        num_teams = random.randint(30, 40)

        statuses = ['forming', 'ready', 'submitted', 'verified', 'disqualified']
        status_weights = [0.3, 0.2, 0.2, 0.25, 0.05]  # Most teams forming or verified

        adjectives = ['Awesome', 'Brilliant', 'Creative', 'Dynamic', 'Elite', 'Fast', 'Great', 'Innovative']
        nouns = ['Builders', 'Coders', 'Developers', 'Engineers', 'Hackers', 'Innovators', 'Makers', 'Squad']

        for i in range(num_teams):
            hackathon = random.choice(hackathons)
            name = f"{random.choice(adjectives)} {random.choice(nouns)} {random.randint(1, 999)}"

            team = Team.objects.create(
                hackathon=hackathon,
                name=name,
                slug=slugify(f"{name}-{i}"),
                tagline=fake.catch_phrase(),
                status=random.choices(statuses, weights=status_weights)[0],
                is_seeking_members=random.choice([True, False]),
                final_score=Decimal(str(random.uniform(0, 100))) if random.random() > 0.3 else Decimal('0.0'),
                technical_score=Decimal(str(random.uniform(0, 100))) if random.random() > 0.5 else Decimal('0.0'),
                commercial_score=Decimal(str(random.uniform(0, 100))) if random.random() > 0.5 else Decimal('0.0'),
                operational_score=Decimal(str(random.uniform(0, 100))) if random.random() > 0.5 else Decimal('0.0'),
            )
            teams.append(team)

        return teams

    def generate_team_members(self, teams, users):
        """Generate 80-120 team members with proper role distribution."""
        team_members = []
        roles = ['hacker', 'hipster', 'hustler', 'mentor']

        for team in teams:
            # Each team gets 2-5 members
            num_members = random.randint(2, min(5, len(users)))
            selected_users = random.sample(users, k=num_members)

            for idx, user in enumerate(selected_users):
                # First member is usually the leader
                is_leader = (idx == 0)

                # Prefer user's preferred role, or assign random
                role = user.preferred_role if user.preferred_role in roles else random.choice(roles)

                try:
                    member = TeamMember.objects.create(
                        team=team,
                        user=user,
                        role=role,
                        is_leader=is_leader,
                    )
                    team_members.append(member)
                except Exception:
                    # Skip if user already in this team
                    pass

        return team_members

    def generate_submissions(self, users, teams, quests, hackathons):
        """Generate 100-150 submissions with varied statuses."""
        submissions = []
        num_submissions = random.randint(100, 150)

        verification_statuses = ['pending', 'verified', 'rejected']
        status_weights = [0.3, 0.5, 0.2]  # Most verified, some pending, few rejected

        for i in range(num_submissions):
            # 60% quest submissions (individual), 40% hackathon submissions (team)
            is_quest = random.random() < 0.6

            if is_quest:
                # Quest submission (individual)
                quest = random.choice(quests)
                user = random.choice(users)
                team = None
                hackathon = None
                submission_url = f"https://github.com/{user.username}/quest-{quest.slug}"
            else:
                # Hackathon submission (team)
                team = random.choice(teams)
                user = None
                quest = None
                hackathon = team.hackathon
                submission_url = f"https://github.com/{team.slug}/project-{i}"

            verification_status = random.choices(verification_statuses, weights=status_weights)[0]

            # Score only if verified
            score = Decimal(str(random.uniform(60, 100))) if verification_status == 'verified' else None

            submission = Submission.objects.create(
                user=user,
                team=team,
                quest=quest,
                hackathon=hackathon,
                submission_url=submission_url,
                description=fake.paragraph(nb_sentences=2),
                verification_status=verification_status,
                score=score,
                feedback=fake.sentence() if verification_status != 'pending' else '',
                attempt_number=random.randint(1, 3),
            )

            # Set verified_at for non-pending submissions
            if verification_status != 'pending':
                submission.verified_at = timezone.now() - timedelta(days=random.randint(1, 30))
                submission.save()

            submissions.append(submission)

        return submissions
