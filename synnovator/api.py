"""
Wagtail API v2 configuration.

Provides REST API endpoints for pages, images, and documents
with support for locale filtering and custom serializers.
"""
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.images.api.v2.views import ImagesAPIViewSet
from wagtail.documents.api.v2.views import DocumentsAPIViewSet

# Create the API router
api_router = WagtailAPIRouter('wagtailapi')

# Register API endpoints
api_router.register_endpoint('pages', PagesAPIViewSet)
api_router.register_endpoint('images', ImagesAPIViewSet)
api_router.register_endpoint('documents', DocumentsAPIViewSet)
