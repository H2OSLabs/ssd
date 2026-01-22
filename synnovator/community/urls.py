"""
URL configuration for community app.
"""
from django.urls import path

from . import views

app_name = 'community'

urlpatterns = [
    path('teams/', views.team_list, name='team_list'),
    path('teams/create/', views.create_team, name='create_team'),
    path('teams/<slug:slug>/', views.team_detail, name='team_detail'),
    path('teams/<slug:slug>/join/', views.join_team, name='join_team'),
    path('teams/<slug:slug>/leave/', views.leave_team, name='leave_team'),
    path('teams/<slug:slug>/members/<int:user_id>/remove/', views.remove_member, name='remove_member'),
]
