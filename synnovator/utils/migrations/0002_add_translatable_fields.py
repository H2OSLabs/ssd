# Generated manually for wagtail-localize
import uuid
import django.db.models.deletion
from django.db import migrations, models


def populate_locale_and_translation_key(apps, schema_editor):
    """Populate locale and translation_key for existing records."""
    Locale = apps.get_model('wagtailcore', 'Locale')
    AuthorSnippet = apps.get_model('utils', 'AuthorSnippet')
    ArticleTopic = apps.get_model('utils', 'ArticleTopic')
    Statistic = apps.get_model('utils', 'Statistic')
    SocialMediaSettings = apps.get_model('utils', 'SocialMediaSettings')
    SystemMessagesSettings = apps.get_model('utils', 'SystemMessagesSettings')

    try:
        en_locale = Locale.objects.get(language_code='en')
    except Locale.DoesNotExist:
        # If no locale exists, create one
        en_locale = Locale.objects.create(language_code='en')

    # Update all existing records
    for model in [AuthorSnippet, ArticleTopic, Statistic, SocialMediaSettings, SystemMessagesSettings]:
        for obj in model.objects.all():
            if not obj.locale_id:
                obj.locale_id = en_locale.id
            if not obj.translation_key:
                obj.translation_key = uuid.uuid4()
            obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0001_initial'),
        ('wagtailcore', '0098_delete_embed'),
    ]

    operations = [
        # Step 1: Add nullable fields
        migrations.AddField(
            model_name='authorsnippet',
            name='locale',
            field=models.ForeignKey(
                null=True,
                editable=False,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='wagtailcore.locale',
                verbose_name='locale'
            ),
        ),
        migrations.AddField(
            model_name='authorsnippet',
            name='translation_key',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='articletopic',
            name='locale',
            field=models.ForeignKey(
                null=True,
                editable=False,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='wagtailcore.locale',
                verbose_name='locale'
            ),
        ),
        migrations.AddField(
            model_name='articletopic',
            name='translation_key',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='statistic',
            name='locale',
            field=models.ForeignKey(
                null=True,
                editable=False,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='wagtailcore.locale',
                verbose_name='locale'
            ),
        ),
        migrations.AddField(
            model_name='statistic',
            name='translation_key',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='socialmediasettings',
            name='locale',
            field=models.ForeignKey(
                null=True,
                editable=False,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='wagtailcore.locale',
                verbose_name='locale'
            ),
        ),
        migrations.AddField(
            model_name='socialmediasettings',
            name='translation_key',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='systemmessagessettings',
            name='locale',
            field=models.ForeignKey(
                null=True,
                editable=False,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='wagtailcore.locale',
                verbose_name='locale'
            ),
        ),
        migrations.AddField(
            model_name='systemmessagessettings',
            name='translation_key',
            field=models.UUIDField(null=True, editable=False),
        ),

        # Step 2: Populate data
        migrations.RunPython(populate_locale_and_translation_key, migrations.RunPython.noop),

        # Step 3: Make fields non-nullable
        migrations.AlterField(
            model_name='authorsnippet',
            name='locale',
            field=models.ForeignKey(
                editable=False,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='wagtailcore.locale',
                verbose_name='locale'
            ),
        ),
        migrations.AlterField(
            model_name='authorsnippet',
            name='translation_key',
            field=models.UUIDField(editable=False),
        ),
        migrations.AlterField(
            model_name='articletopic',
            name='locale',
            field=models.ForeignKey(
                editable=False,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='wagtailcore.locale',
                verbose_name='locale'
            ),
        ),
        migrations.AlterField(
            model_name='articletopic',
            name='translation_key',
            field=models.UUIDField(editable=False),
        ),
        migrations.AlterField(
            model_name='statistic',
            name='locale',
            field=models.ForeignKey(
                editable=False,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='wagtailcore.locale',
                verbose_name='locale'
            ),
        ),
        migrations.AlterField(
            model_name='statistic',
            name='translation_key',
            field=models.UUIDField(editable=False),
        ),
        migrations.AlterField(
            model_name='socialmediasettings',
            name='locale',
            field=models.ForeignKey(
                editable=False,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='wagtailcore.locale',
                verbose_name='locale'
            ),
        ),
        migrations.AlterField(
            model_name='socialmediasettings',
            name='translation_key',
            field=models.UUIDField(editable=False),
        ),
        migrations.AlterField(
            model_name='systemmessagessettings',
            name='locale',
            field=models.ForeignKey(
                editable=False,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='wagtailcore.locale',
                verbose_name='locale'
            ),
        ),
        migrations.AlterField(
            model_name='systemmessagessettings',
            name='translation_key',
            field=models.UUIDField(editable=False),
        ),

        # Step 4: Add unique constraints
        migrations.AlterUniqueTogether(
            name='authorsnippet',
            unique_together={('translation_key', 'locale')},
        ),
        migrations.AlterUniqueTogether(
            name='articletopic',
            unique_together={('translation_key', 'locale')},
        ),
        migrations.AlterUniqueTogether(
            name='statistic',
            unique_together={('translation_key', 'locale')},
        ),
        migrations.AlterUniqueTogether(
            name='socialmediasettings',
            unique_together={('translation_key', 'locale')},
        ),
        migrations.AlterUniqueTogether(
            name='systemmessagessettings',
            unique_together={('translation_key', 'locale')},
        ),
    ]
