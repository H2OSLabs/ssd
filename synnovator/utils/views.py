"""Test views for layout components."""
from django.views.generic import TemplateView


class ThreePaneLayoutTestView(TemplateView):
    """Test view for three-pane layout."""

    template_name = "test/three_pane_test.html"
