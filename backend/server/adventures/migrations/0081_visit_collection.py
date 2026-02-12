# Generated manually for adding collection field to Visit

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('adventures', '0080_add_cached_average_rating'),
    ]

    operations = [
        migrations.AddField(
            model_name='visit',
            name='collection',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='planned_visits',
                to='adventures.collection'
            ),
        ),
    ]
