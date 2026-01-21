from django.urls import path
from . import views

app_name = 'hackathons'

urlpatterns = [
    # Team management
    path('teams/', views.team_list, name='teams'),
    path('teams/create/', views.create_team, name='create_team'),
    path('teams/<slug:slug>/join/', views.join_team, name='join_team'),

    # Quest submissions
    path('quests/<slug:slug>/submit/', views.submit_quest, name='submit_quest'),

    # Hackathon actions
    path('<slug:slug>/register/', views.register_hackathon, name='register'),
    path('<slug:slug>/submit/', views.submit_project, name='submit'),

    # P2: Calendar API
    path('api/calendar/events/', views.calendar_events_api, name='calendar_events'),
    path('api/hackathon/<int:hackathon_id>/timeline/', views.hackathon_timeline_api, name='hackathon_timeline'),
]
