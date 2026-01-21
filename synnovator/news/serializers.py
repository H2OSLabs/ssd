"""
Custom serializers for News/Blog API.

Handles proper serialization of StreamField content, images, and related models.
"""

from rest_framework import serializers
from wagtail.api.v2.serializers import PageSerializer
from wagtail.images.api.fields import ImageRenditionField


class AuthorSerializer(serializers.Serializer):
    """Serializer for AuthorSnippet."""
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    image = ImageRenditionField('fill-100x100', read_only=True, source='image')
    image_original = serializers.SerializerMethodField()

    def get_image_original(self, obj):
        """Get original image URL."""
        if obj.image:
            return {
                'id': obj.image.id,
                'url': obj.image.file.url,
                'width': obj.image.width,
                'height': obj.image.height,
                'alt': obj.image.default_alt_text,
            }
        return None


class TopicSerializer(serializers.Serializer):
    """Serializer for ArticleTopic."""
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    slug = serializers.SlugField(read_only=True)


class RelatedPageSerializer(serializers.Serializer):
    """Serializer for related pages."""
    id = serializers.IntegerField(read_only=True, source='page.id')
    title = serializers.CharField(read_only=True, source='page.title')
    slug = serializers.CharField(read_only=True, source='page.slug')
    url = serializers.CharField(read_only=True, source='page.url')
    listing_image = ImageRenditionField('fill-600x400', read_only=True, source='page.listing_image')


class ArticlePageSerializer(PageSerializer):
    """
    Custom serializer for ArticlePage with proper StreamField handling.

    Provides:
    - Nested author information with image
    - Topic metadata
    - Rendered StreamField body (HTML + structured data)
    - Featured image with multiple renditions
    - Related articles
    - Locale information for i18n
    """

    # Custom fields for author and topic
    author = AuthorSerializer(read_only=True)
    topic = TopicSerializer(read_only=True)

    # Display date property
    display_date = serializers.CharField(read_only=True)

    # Locale information for i18n
    locale = serializers.CharField(
        read_only=True,
        source='locale.language_code'
    )

    # Available translations for language switcher
    available_translations = serializers.SerializerMethodField()

    # Listing image with multiple renditions for Next.js
    listing_image_thumbnail = ImageRenditionField('fill-400x300', source='listing_image', read_only=True)
    listing_image_medium = ImageRenditionField('fill-800x600', source='listing_image', read_only=True)
    listing_image_large = ImageRenditionField('fill-1200x900', source='listing_image', read_only=True)
    listing_image_original = serializers.SerializerMethodField()

    # Featured image from StreamField (first image block)
    featured_image = serializers.SerializerMethodField()

    # Related pages
    related_articles = RelatedPageSerializer(many=True, read_only=True, source='page_related_pages')

    # Social image for og:image
    social_image_url = serializers.SerializerMethodField()

    def get_listing_image_original(self, obj):
        """Get original listing image data."""
        if obj.listing_image:
            return {
                'id': obj.listing_image.id,
                'url': obj.listing_image.file.url,
                'width': obj.listing_image.width,
                'height': obj.listing_image.height,
                'alt': obj.listing_image.default_alt_text,
            }
        return None

    def get_featured_image(self, obj):
        """
        Extract featured image from StreamField.
        Returns the first image block if exists.
        """
        if obj.image and len(obj.image) > 0:
            image_block = obj.image[0]
            if image_block.block_type == 'image':
                image_data = image_block.value
                if image_data and image_data.get('image'):
                    img = image_data['image']
                    return {
                        'id': img.id,
                        'url': img.file.url,
                        'width': img.width,
                        'height': img.height,
                        'alt': image_data.get('image_alt_text') or img.default_alt_text,
                        'caption': image_data.get('caption', ''),
                        # Provide multiple renditions
                        'renditions': {
                            'thumbnail': self._get_rendition_url(img, 'fill-400x300'),
                            'medium': self._get_rendition_url(img, 'fill-800x600'),
                            'large': self._get_rendition_url(img, 'fill-1200x900'),
                            'original': img.file.url,
                        }
                    }
        return None

    def get_social_image_url(self, obj):
        """Get social image URL for og:image meta tag."""
        if obj.social_image:
            # Generate a 1200x630 rendition for social media
            rendition = obj.social_image.get_rendition('fill-1200x630')
            return rendition.url
        elif obj.listing_image:
            rendition = obj.listing_image.get_rendition('fill-1200x630')
            return rendition.url
        return None

    def _get_rendition_url(self, image, filter_spec):
        """Helper to get rendition URL safely."""
        try:
            rendition = image.get_rendition(filter_spec)
            return rendition.url
        except Exception:
            return image.file.url

    def get_available_translations(self, obj):
        """
        Return available language versions of this page.
        Used for language switcher in frontend.
        """
        return [
            {
                'locale': trans.locale.language_code,
                'title': trans.title,
                'url': trans.url,
            }
            for trans in obj.get_translations().live()
        ]
