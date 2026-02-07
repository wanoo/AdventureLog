# Generated for adding Transportation and Lodging to Visit model

from django.db import migrations, models, connection
import django.db.models.deletion


def column_exists(table, column):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
        """, [table, column])
        return cursor.fetchone() is not None


def add_field_if_not_exists(apps, schema_editor):
    """Add transportation and lodging fields if they don't already exist."""
    if not column_exists('adventures_visit', 'transportation_id'):
        schema_editor.execute("""
            ALTER TABLE adventures_visit
            ADD COLUMN transportation_id uuid NULL
            REFERENCES adventures_transportation(id) ON DELETE CASCADE
        """)

    if not column_exists('adventures_visit', 'lodging_id'):
        schema_editor.execute("""
            ALTER TABLE adventures_visit
            ADD COLUMN lodging_id uuid NULL
            REFERENCES adventures_lodging(id) ON DELETE CASCADE
        """)


def noop(apps, schema_editor):
    pass


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
        # Add transportation and lodging FKs if they don't exist
        migrations.RunPython(add_field_if_not_exists, noop),
    ]
