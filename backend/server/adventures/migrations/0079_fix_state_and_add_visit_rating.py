# Migration to fix Django's migration state and add rating to Visit
#
# The 0077 migration used raw SQL to remove collection FK columns from
# Transportation and Lodging, but Django's migration state wasn't updated.
# This migration uses SeparateDatabaseAndState to update Django's state
# without running any SQL (since columns are already gone).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adventures', '0078_merge_20260207'),
    ]

    operations = [
        # Fix Django's state for Transportation.collection FK removal
        # The column was already dropped by 0077's raw SQL
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name='transportation',
                    name='collection',
                ),
            ],
            database_operations=[],  # No DB changes - column already gone
        ),

        # Fix Django's state for Lodging.collection FK removal
        # The column was already dropped by 0077's raw SQL
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name='lodging',
                    name='collection',
                ),
            ],
            database_operations=[],  # No DB changes - column already gone
        ),

        # Add rating field to Visit
        migrations.AddField(
            model_name='visit',
            name='rating',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
