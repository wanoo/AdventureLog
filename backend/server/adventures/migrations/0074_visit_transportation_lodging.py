# Generated for adding Transportation and Lodging to Visit model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('adventures', '0073_populate_visit_users'),
    ]

    operations = [
        # Make location nullable since visits can now be for transportation/lodging
        migrations.AlterField(
            model_name='visit',
            name='location',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='visits',
                to='adventures.location'
            ),
        ),
        # Add transportation FK
        migrations.AddField(
            model_name='visit',
            name='transportation',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='visits',
                to='adventures.transportation'
            ),
        ),
        # Add lodging FK
        migrations.AddField(
            model_name='visit',
            name='lodging',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='visits',
                to='adventures.lodging'
            ),
        ),
    ]
