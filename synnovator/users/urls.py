from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('preferences/notifications/', views.notification_preferences, name='notification_preferences'),
    path('<str:username>/', views.user_profile, name='profile'),
]
