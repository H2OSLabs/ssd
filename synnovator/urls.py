from django.conf import settings
from django.urls import include, path
from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

from synnovator.search import views as search_views
from synnovator.api import api_router

# URLs without language prefix (admin, API, static files)
urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("api/v2/", api_router.urls),
    path("i18n/setlang/", set_language, name="set_language"),
]

# Debug toolbar for development
if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    import debug_toolbar

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns

# URLs with language prefix (public-facing pages)
urlpatterns += i18n_patterns(
    path("search/", search_views.search, name="search"),
    path("hackathons/", include("synnovator.hackathons.urls")),
    path("utils/", include("synnovator.utils.urls")),
    path("", include(wagtail_urls)),
    prefix_default_language=True,  # Both /en/ and /zh-hans/ in URLs
)
