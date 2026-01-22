from django.urls import path
from . import views

app_name = 'hackathons'

urlpatterns = [
    # Hackathon Index Pages (via Wagtail)
    path('', views.hackathon_index, name='index'),
    path('in-progress/', views.hackathon_in_progress, name='in_progress'),

    # Legacy hackathon listing (redirects to Wagtail HackathonIndexPage)
    path('all/', views.hackathon_list, name='list'),

    # Team management
    path('teams/', views.team_list, name='teams'),
    path('<slug:hackathon_slug>/teams/', views.team_list, name='hackathon_teams'),
    path('teams/find/', views.team_formation, name='team_formation'),
    path('teams/create/', views.create_team, name='create_team'),
    path('teams/<slug:slug>/', views.team_detail, name='team_detail'),
    path('teams/<slug:slug>/join/', views.join_team, name='join_team'),

    # Quest pages
    path('quests/', views.quest_list, name='quest_list'),
    path('quests/<slug:slug>/', views.quest_detail, name='quest_detail'),
    path('quests/<slug:slug>/submit/', views.submit_quest, name='submit_quest'),

    # Submission pages
    path('submissions/', views.submission_list, name='submission_list'),

    # Hackathon actions
    path('<slug:slug>/register/', views.register_hackathon, name='register'),
    path('<slug:slug>/submit/', views.submit_project, name='submit'),

    # P2: Calendar API
    path('api/calendar/events/', views.calendar_events_api, name='calendar_events'),
    path('api/hackathon/<int:hackathon_id>/timeline/', views.hackathon_timeline_api, name='hackathon_timeline'),
]
