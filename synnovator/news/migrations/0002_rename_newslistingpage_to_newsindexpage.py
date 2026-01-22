# Generated manually for model rename

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0001_initial'),
        ('wagtailcore', '0091_remove_revision_submitted_for_moderation'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='NewsListingPage',
            new_name='NewsIndexPage',
        ),
    ]
