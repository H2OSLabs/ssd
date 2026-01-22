from django.db import models
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel, HelpPanel
from wagtail.search import index

from wagtail.fields import StreamField
from synnovator.utils.blocks import StoryBlock, InternalLinkBlock
from synnovator.utils.models import BasePage


class HomePage(BasePage):
    """
    Home page model with configurable content sections.

    Admins can configure which IndexPages (NewsIndexPage, HackathonIndexPage)
    to display in the News and Hackathons sections. This removes hardcoded
    content and allows flexible configuration through the Wagtail admin.
    """
    template = "pages/home_page.html"
    introduction = models.TextField(blank=True)
    hero_cta = StreamField(
        [("link", InternalLinkBlock())],
        blank=True,
        min_num=0,
        max_num=1,
    )
    body = StreamField(StoryBlock())
    featured_section_title = models.TextField(blank=True)

    # Configurable News Section
    news_section_title = models.CharField(
        max_length=200,
        default="Latest News",
        help_text="Title for the news section on the home page"
    )
    news_section_page = models.ForeignKey(
        'news.NewsIndexPage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Select the News Index Page to display articles from"
    )
    news_items_count = models.PositiveIntegerField(
        default=3,
        help_text="Number of news articles to display"
    )

    # Configurable Hackathons Section
    hackathons_section_title = models.CharField(
        max_length=200,
        default="Featured Hackathons",
        help_text="Title for the hackathons section on the home page"
    )
    hackathons_section_page = models.ForeignKey(
        'hackathons.HackathonIndexPage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Select the Hackathon Index Page to display hackathons from"
    )
    hackathons_items_count = models.PositiveIntegerField(
        default=3,
        help_text="Number of hackathons to display"
    )

    # Stats Section (configurable)
    show_stats_section = models.BooleanField(
        default=True,
        help_text="Show the statistics section (active hackathons, teams, quests)"
    )

    search_fields = BasePage.search_fields + [index.SearchField("introduction")]

    content_panels = BasePage.content_panels + [
        FieldPanel("introduction"),
        FieldPanel("hero_cta"),
        MultiFieldPanel(
            [
                FieldPanel("show_stats_section"),
            ],
            heading="Stats Section",
        ),
        MultiFieldPanel(
            [
                FieldPanel("news_section_title"),
                FieldPanel("news_section_page"),
                FieldPanel("news_items_count"),
            ],
            heading="News Section",
        ),
        MultiFieldPanel(
            [
                FieldPanel("hackathons_section_title"),
                FieldPanel("hackathons_section_page"),
                FieldPanel("hackathons_items_count"),
            ],
            heading="Hackathons Section",
        ),
        FieldPanel("body"),
        MultiFieldPanel(
            [
                FieldPanel("featured_section_title", heading="Title"),
                InlinePanel(
                    "page_related_pages",
                    label="Pages",
                    max_num=12,
                ),
            ],
            heading="Featured section",
        ),
    ]

    def get_context(self, request, *args, **kwargs):
        """Add news articles and hackathons to template context."""
        context = super().get_context(request, *args, **kwargs)

        # Get news articles from configured NewsIndexPage
        news_articles = []
        if self.news_section_page:
            from synnovator.news.models import ArticlePage
            from django.db.models.functions import Coalesce
            news_articles = (
                ArticlePage.objects.live()
                .public()
                .descendant_of(self.news_section_page)
                .annotate(date=Coalesce("publication_date", "first_published_at"))
                .select_related("listing_image", "author", "topic")
                .order_by("-date")[:self.news_items_count]
            )
        context['news_articles'] = news_articles
        context['news_section_title'] = self.news_section_title
        context['news_section_url'] = self.news_section_page.url if self.news_section_page else None

        # Get hackathons from configured HackathonIndexPage
        hackathons = []
        if self.hackathons_section_page:
            hackathons = self.hackathons_section_page.get_filtered_hackathons()[:self.hackathons_items_count]
        context['hackathons'] = hackathons
        context['hackathons_section_title'] = self.hackathons_section_title
        context['hackathons_section_url'] = self.hackathons_section_page.url if self.hackathons_section_page else None

        # Get stats
        if self.show_stats_section:
            from synnovator.hackathons.models import HackathonPage, Team, Quest
            from synnovator.hackathons.models.submission import Submission
            context['stats'] = {
                'active_hackathons': HackathonPage.objects.filter(status='in_progress').count(),
                'teams_formed': Team.objects.count(),
                'quests_completed': Submission.objects.filter(verification_status='verified', quest__isnull=False).count(),
            }
        else:
            context['stats'] = None

        return context
