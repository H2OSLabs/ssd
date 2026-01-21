"""
User asset and gamification models.
Implements P2 requirement for virtual asset management and user rewards.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet


class UserAsset(models.Model):
    """
    Virtual assets owned by users (badges, achievements, rewards).
    Supports gamification and user engagement.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assets',
        verbose_name=_("User")
    )

    asset_type = models.CharField(
        max_length=50,
        choices=[
            ('badge', _('Badge')),
            ('achievement', _('Achievement')),
            ('coin', _('Coin')),
            ('token', _('Token')),
            ('nft', _('NFT')),
        ],
        verbose_name=_("Asset Type"),
        db_index=True
    )

    asset_id = models.CharField(
        max_length=200,
        verbose_name=_("Asset ID"),
        help_text=_("Identifier for specific asset (e.g., 'first_place_badge')")
    )

    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Quantity"),
        help_text=_("Number of this asset owned")
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadata"),
        help_text=_("Additional asset properties (rarity, description, image_url)")
    )

    acquired_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Acquired At")
    )

    class Meta:
        unique_together = [['user', 'asset_type', 'asset_id']]
        ordering = ['-acquired_at']
        verbose_name = _("User Asset")
        verbose_name_plural = _("User Assets")
        indexes = [
            models.Index(fields=['user', 'asset_type']),
            models.Index(fields=['asset_type', 'asset_id']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.asset_id} ({self.quantity}x)"


@register_snippet
class AssetTransaction(models.Model):
    """
    Tracks asset transactions for audit trail and analytics.
    Records all asset acquisitions, transfers, and redemptions.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='asset_transactions',
        verbose_name=_("User")
    )

    transaction_type = models.CharField(
        max_length=50,
        choices=[
            ('earn', _('Earned')),
            ('purchase', _('Purchased')),
            ('transfer_in', _('Received Transfer')),
            ('transfer_out', _('Sent Transfer')),
            ('redeem', _('Redeemed')),
            ('expire', _('Expired')),
        ],
        verbose_name=_("Transaction Type"),
        db_index=True
    )

    asset_type = models.CharField(
        max_length=50,
        verbose_name=_("Asset Type")
    )

    asset_id = models.CharField(
        max_length=200,
        verbose_name=_("Asset ID")
    )

    quantity = models.IntegerField(
        verbose_name=_("Quantity"),
        help_text=_("Positive for gain, negative for loss")
    )

    # Related objects (optional)
    related_submission = models.ForeignKey(
        'hackathons.Submission',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Related Submission"),
        help_text=_("Submission that triggered this transaction")
    )

    related_quest = models.ForeignKey(
        'hackathons.Quest',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Related Quest")
    )

    # Transfer details (for transfer transactions)
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='asset_transfers_sent',
        verbose_name=_("From User")
    )

    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='asset_transfers_received',
        verbose_name=_("To User")
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Transaction description")
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadata")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )

    panels = [
        FieldPanel('user'),
        FieldPanel('transaction_type'),
        FieldPanel('asset_type'),
        FieldPanel('asset_id'),
        FieldPanel('quantity'),
        FieldPanel('description'),
    ]

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Asset Transaction")
        verbose_name_plural = _("Asset Transactions")
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['transaction_type', '-created_at']),
            models.Index(fields=['asset_type', 'asset_id']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_transaction_type_display()} {self.quantity}x {self.asset_id}"

    @classmethod
    def award_asset(cls, user, asset_type, asset_id, quantity=1, reason="", related_submission=None, related_quest=None):
        """Award an asset to a user"""
        # Create transaction
        transaction = cls.objects.create(
            user=user,
            transaction_type='earn',
            asset_type=asset_type,
            asset_id=asset_id,
            quantity=quantity,
            description=reason,
            related_submission=related_submission,
            related_quest=related_quest,
        )

        # Update user asset
        asset, created = UserAsset.objects.get_or_create(
            user=user,
            asset_type=asset_type,
            asset_id=asset_id,
            defaults={'quantity': quantity}
        )
        if not created:
            asset.quantity += quantity
            asset.save()

        # Invalidate cache
        cache.delete(f'user_assets:{user.id}')

        return transaction
