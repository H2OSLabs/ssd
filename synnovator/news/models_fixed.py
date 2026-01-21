# news/models.py - 修复后的版本
from django.conf import settings
from django.db import models
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel, HelpPanel
from wagtail.search import index
from wagtail.api import APIField

from synnovator.utils.models import BasePage, ArticleTopic
from synnovator.utils.blocks import StoryBlock, CaptionedImageBlock


class NewsIndexPage(BasePage):
    """
    新闻列表页面

    修复问题：
    1. 继承 BasePage 而不是 Page（获得 SEO/social/listing 功能）
    2. intro 使用 RichTextField 而不是 blocks.RichTextBlock()
    3. 添加分页功能避免性能问题
    4. 使用 select_related/public() 优化查询
    5. 添加页面关系配置
    """
    template = "pages/news_listing_page.html"
    subpage_types = ["news.NewsArticle"]
    max_count = 1  # 只允许一个新闻列表页

    intro = RichTextField(
        blank=True,
        features=["bold", "italic", "link"],
        help_text="Introduction text displayed at the top of the news listing."
    )

    content_panels = BasePage.content_panels + [
        FieldPanel("intro"),
        HelpPanel("This page will automatically display child Article pages."),
    ]

    search_fields = BasePage.search_fields + [
        index.SearchField("intro")
    ]

    def paginate_queryset(self, queryset, request):
        """分页查询集"""
        page_number = request.GET.get("page", 1)
        paginator = Paginator(queryset, settings.DEFAULT_PER_PAGE)
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        return (paginator, page, page.object_list, page.has_other_pages())

    def get_context(self, request, *args, **kwargs):
        """
        修复性能问题：
        - 使用 select_related() 减少数据库查询（N+1 问题）
        - 使用 public() 过滤已发布内容
        - 使用 Coalesce 统一日期排序
        - 添加分页
        """
        context = super().get_context(request, *args, **kwargs)

        # 优化的查询集
        queryset = (
            NewsArticle.objects.live()
            .public()
            .annotate(
                date=Coalesce("publication_date", "first_published_at"),
            )
            .select_related("listing_image", "author", "topic")  # 修复 N+1 查询
            .order_by("-date")
        )

        # 主题筛选
        article_topics = ArticleTopic.objects.filter(
            news_articles__isnull=False
        ).values("title", "slug").distinct().order_by("title")
        matching_topic = False

        topic_query_param = request.GET.get("topic")
        if topic_query_param and topic_query_param in article_topics.values_list(
            "slug", flat=True
        ):
            matching_topic = topic_query_param
            queryset = queryset.filter(topic__slug=topic_query_param)

        # 分页
        paginator, page, _object_list, is_paginated = self.paginate_queryset(
            queryset, request
        )
        context["paginator"] = paginator
        context["paginator_page"] = page
        context["is_paginated"] = is_paginated

        # 主题列表
        context["topics"] = article_topics
        context["matching_topic"] = matching_topic

        return context


class NewsArticle(BasePage):
    """
    新闻文章页面

    修复问题：
    1. 使用 ForeignKey 关联 AuthorSnippet 而不是 CharField
    2. 使用 topic (ForeignKey) 而不是 category (CharField)
    3. publication_date 使用 DateTimeField 而不是 DateField
    4. body 使用项目的 StoryBlock 而不是自定义 StreamField
    5. 添加 image、introduction 等标准字段
    6. API 字段包含所有必要的序列化字段
    7. 添加 display_date 属性用于格式化日期
    """
    template = "pages/article_page.html"
    parent_page_types = ["news.NewsIndexPage"]

    author = models.ForeignKey(
        "utils.AuthorSnippet",
        blank=False,
        null=False,
        on_delete=models.deletion.PROTECT,
        related_name="+",
        help_text="Select the author of this article."
    )

    topic = models.ForeignKey(
        "utils.ArticleTopic",
        blank=False,
        null=False,
        on_delete=models.deletion.PROTECT,
        related_name="news_articles",
        help_text="Categorize this article by topic."
    )

    publication_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Use this field to override the date that the "
        "news item appears to have been published.",
    )

    introduction = models.TextField(
        blank=True,
        help_text="Brief summary of the article for listings and search results."
    )

    image = StreamField(
        [("image", CaptionedImageBlock())],
        blank=True,
        max_num=1,
        help_text="Main article image with optional caption."
    )

    body = StreamField(
        StoryBlock(),
        help_text="Main article content."
    )

    featured_section_title = models.TextField(
        blank=True,
        help_text="Title for the featured articles section at the bottom."
    )

    # 搜索配置
    search_fields = BasePage.search_fields + [
        index.SearchField("introduction"),
        index.FilterField("topic"),
        index.FilterField("publication_date"),
    ]

    # API 字段配置（修复前端数据格式问题）
    api_fields = [
        APIField('author'),  # 自动序列化为 AuthorSnippet 对象
        APIField('topic'),   # 自动序列化为 ArticleTopic 对象
        APIField('publication_date'),
        APIField('display_date'),  # 格式化的日期字符串
        APIField('introduction'),
        APIField('image'),
        APIField('body'),
        APIField('featured_section_title'),
        # BasePage 提供的字段
        APIField('listing_image'),
        APIField('listing_title'),
        APIField('listing_summary'),
        APIField('social_image'),
        APIField('social_text'),
    ]

    # 内容面板配置
    content_panels = BasePage.content_panels + [
        FieldPanel("author"),
        FieldPanel("publication_date"),
        FieldPanel("topic"),
        FieldPanel("introduction"),
        FieldPanel("image"),
        FieldPanel("body"),
        MultiFieldPanel(
            [
                FieldPanel("featured_section_title", heading="Title"),
                InlinePanel(
                    "page_related_pages",
                    label="Pages",
                    max_num=3,
                ),
            ],
            heading="Featured section",
        ),
    ]

    @property
    def display_date(self):
        """
        格式化的日期字符串用于显示
        优先使用 publication_date，否则使用 first_published_at
        """
        if self.publication_date:
            return self.publication_date.strftime("%d %b %Y")
        elif self.first_published_at:
            return self.first_published_at.strftime("%d %b %Y")
        return None
