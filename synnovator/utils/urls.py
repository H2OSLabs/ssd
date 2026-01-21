"""URL patterns for utils app (test views)."""
from django.conf import settings
from django.urls import path

from .views import ThreePaneLayoutTestView, ComponentTestView

app_name = "utils"

urlpatterns = []

# Only register test views in DEBUG mode
if settings.DEBUG:
    urlpatterns += [
        path("test/three-pane/", ThreePaneLayoutTestView.as_view(), name="three_pane_test"),
        path("test/components/", ComponentTestView.as_view(), name="component_test"),
    ]
