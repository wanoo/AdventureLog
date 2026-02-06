# Safe migration for adding Transportation and Lodging to Visit model
# This migration uses raw SQL to add columns if they don't exist

from django.db import migrations, connection


def add_columns_if_not_exist(apps, schema_editor):
    """Add transportation_id and lodging_id columns to adventures_visit if they don't exist."""
    with connection.cursor() as cursor:
        # Check if transportation_id column exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'adventures_visit'
                AND column_name = 'transportation_id'
            );
        """)
        transportation_exists = cursor.fetchone()[0]

        if not transportation_exists:
            cursor.execute("""
                ALTER TABLE adventures_visit
                ADD COLUMN transportation_id UUID NULL
                REFERENCES adventures_transportation(id) ON DELETE CASCADE;
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS adventures_visit_transportation_id_idx
                ON adventures_visit (transportation_id);
            """)

        # Check if lodging_id column exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'adventures_visit'
                AND column_name = 'lodging_id'
            );
        """)
        lodging_exists = cursor.fetchone()[0]

        if not lodging_exists:
            cursor.execute("""
                ALTER TABLE adventures_visit
                ADD COLUMN lodging_id UUID NULL
                REFERENCES adventures_lodging(id) ON DELETE CASCADE;
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS adventures_visit_lodging_id_idx
                ON adventures_visit (lodging_id);
            """)

        # Make location_id nullable if it isn't already
        cursor.execute("""
            ALTER TABLE adventures_visit
            ALTER COLUMN location_id DROP NOT NULL;
        """)


def reverse_migration(apps, schema_editor):
    """Remove the columns (for rollback)."""
    with connection.cursor() as cursor:
        cursor.execute("ALTER TABLE adventures_visit DROP COLUMN IF EXISTS transportation_id;")
        cursor.execute("ALTER TABLE adventures_visit DROP COLUMN IF EXISTS lodging_id;")


class Migration(migrations.Migration):

    dependencies = [
        ('adventures', '0076_visit_transportation_lodging'),
    ]

    operations = [
        migrations.RunPython(add_columns_if_not_exist, reverse_migration),
    ]
