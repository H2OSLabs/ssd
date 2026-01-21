from django.db import migrations, models
import django.db.models.deletion
import wagtail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0094_alter_page_locale'),
        ('navigation', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='navigationsettings',
            name='locale',
            field=models.ForeignKey(default=1, editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='wagtailcore.locale'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='navigationsettings',
            name='translation_key',
            field=models.UUIDField(default='00000000-0000-0000-0000-000000000000', editable=False),
            preserve_default=False,
        ),
    ]
