# Generated manually for HackathonIndexPage refactoring

import django.db.models.deletion
import wagtail.fields
from django.db import migrations, models


def copy_intro_to_introduction(apps, schema_editor):
    """Copy intro field values to introduction field"""
    HackathonIndexPage = apps.get_model('hackathons', 'HackathonIndexPage')
    for page in HackathonIndexPage.objects.all():
        if page.intro:
            page.introduction = page.intro
            page.save(update_fields=['introduction'])


class Migration(migrations.Migration):

    dependencies = [
        ('hackathons', '0005_hackathonindexpage'),
        ('images', '0001_initial'),
        ('wagtailcore', '0098_delete_embed'),
    ]

    operations = [
        # Add BasePage fields
        migrations.AddField(
            model_name='hackathonindexpage',
            name='social_text',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='hackathonindexpage',
            name='listing_title',
            field=models.CharField(blank=True, help_text='Override the page title used when this page appears in listings', max_length=255),
        ),
        migrations.AddField(
            model_name='hackathonindexpage',
            name='listing_summary',
            field=models.CharField(blank=True, help_text="The text summary used when this page appears in listings. It's also used as the description for search engines if the 'Meta description' field above is not defined.", max_length=255),
        ),
        migrations.AddField(
            model_name='hackathonindexpage',
            name='appear_in_search_results',
            field=models.BooleanField(default=True, help_text='Make this page available for indexing by search engines.If unchecked, the page will no longer be indexed by search engines.'),
        ),
        migrations.AddField(
            model_name='hackathonindexpage',
            name='listing_image',
            field=models.ForeignKey(blank=True, help_text='Choose the image you wish to be displayed when this page appears in listings', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='images.customimage'),
        ),
        migrations.AddField(
            model_name='hackathonindexpage',
            name='social_image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='images.customimage'),
        ),
        # Add introduction field (temporarily allow blank)
        migrations.AddField(
            model_name='hackathonindexpage',
            name='introduction',
            field=wagtail.fields.RichTextField(blank=True, features=['bold', 'italic', 'link'], help_text='Introduction text displayed at the top of the hackathons listing page'),
        ),
        # Copy data from intro to introduction
        migrations.RunPython(copy_intro_to_introduction, migrations.RunPython.noop),
        # Remove old intro field
        migrations.RemoveField(
            model_name='hackathonindexpage',
            name='intro',
        ),
    ]
