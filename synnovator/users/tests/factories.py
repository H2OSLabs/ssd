"""
Factory Boy factories for users app.
"""

import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for custom User model."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@test.com")
    password = factory.PostGenerationMethodCall("set_password", "password123")
    preferred_role = "hacker"
    bio = factory.Faker("sentence")
    skills = factory.LazyFunction(lambda: ["Python", "Django"])
    xp_points = 0
    reputation_score = 0
    level = 1
    profile_completed = False
    is_seeking_team = False

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        password = extracted if extracted else "password123"
        self.set_password(password)
        self.save()


class AdminUserFactory(UserFactory):
    """Factory for admin users."""

    username = factory.Sequence(lambda n: f"admin_{n}")
    is_staff = True
    is_superuser = True


class HackerUserFactory(UserFactory):
    """Factory for users with hacker role."""

    preferred_role = "hacker"
    skills = factory.LazyFunction(lambda: ["Python", "JavaScript", "Machine Learning"])


class HipsterUserFactory(UserFactory):
    """Factory for users with hipster (designer) role."""

    preferred_role = "hipster"
    skills = factory.LazyFunction(lambda: ["UI/UX", "Figma", "CSS"])


class HustlerUserFactory(UserFactory):
    """Factory for users with hustler (business) role."""

    preferred_role = "hustler"
    skills = factory.LazyFunction(lambda: ["Business Development", "Marketing", "Pitch"])


class MentorUserFactory(UserFactory):
    """Factory for mentor users."""

    preferred_role = "mentor"
    xp_points = 1000
    level = 11
    profile_completed = True


class ExperiencedUserFactory(UserFactory):
    """Factory for experienced users with high XP."""

    xp_points = 500
    level = 6
    reputation_score = 4.5
    profile_completed = True
