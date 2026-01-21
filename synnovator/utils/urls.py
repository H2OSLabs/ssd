"""URL patterns for utils app (test views)."""
from django.urls import path

from .views import ThreePaneLayoutTestView

app_name = "utils"

urlpatterns = [
    path("test/three-pane/", ThreePaneLayoutTestView.as_view(), name="three_pane_test"),
]
