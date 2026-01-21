# Generated manually for Quest refactoring to Snippet

import django.db.models.deletion
import wagtail.fields
from django.db import migrations, models


def migrate_quest_to_phase(apps, schema_editor):
    """
    Migrate existing Quest.hackathon relationships to Phase.required_quests.
    For each Quest with a hackathon, associate it with the first phase of that hackathon.
    """
    Quest = apps.get_model('hackathons', 'Quest')
    Phase = apps.get_model('hackathons', 'Phase')
    
    # For each Quest that has a hackathon, associate it with the first phase
    for quest in Quest.objects.filter(hackathon__isnull=False):
        hackathon = quest.hackathon
        # Find the first phase of this hackathon
        first_phase = hackathon.phases.first()
        if first_phase:
            first_phase.required_quests.add(quest)


class Migration(migrations.Migration):

    dependencies = [
        ('hackathons', '0006_refactor_hackathonindexpage'),
        ('wagtailcore', '0098_delete_embed'),
    ]

    operations = [
        # Add ManyToMany relationship between Phase and Quest
        migrations.AddField(
            model_name='phase',
            name='required_quests',
            field=models.ManyToManyField(
                blank=True,
                help_text='Quests that must be completed to advance from this phase',
                related_name='phases',
                to='hackathons.quest'
            ),
        ),
        # Add TranslatableMixin fields to Quest (translation_key, locale)
        migrations.AddField(
            model_name='quest',
            name='locale',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to='wagtailcore.locale'
            ),
        ),
        migrations.AddField(
            model_name='quest',
            name='translation_key',
            field=models.UUIDField(editable=False, null=True),
        ),
        # Data migration: migrate quest.hackathon to phase.required_quests
        migrations.RunPython(migrate_quest_to_phase, migrations.RunPython.noop),
        # Remove hackathon ForeignKey from Quest
        migrations.RemoveField(
            model_name='quest',
            name='hackathon',
        ),
        # Remove unique constraint from Quest.slug
        migrations.AlterField(
            model_name='quest',
            name='slug',
            field=models.SlugField(
                help_text='URL-friendly identifier (not required to be globally unique)',
                max_length=200
            ),
        ),
        # Add unique_together constraint for TranslatableMixin
        migrations.AlterUniqueTogether(
            name='quest',
            unique_together={('translation_key', 'locale')},
        ),
    ]
