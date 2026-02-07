# Safe migration for adding tags field to Transportation and Lodging models
# This migration uses raw SQL to add columns if they don't exist

from django.db import migrations, connection


def add_tags_columns_if_not_exist(apps, schema_editor):
    """Add tags column to adventures_transportation and adventures_lodging if they don't exist."""
    with connection.cursor() as cursor:
        # Check if tags column exists on transportation
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'adventures_transportation'
                AND column_name = 'tags'
            );
        """)
        transportation_tags_exists = cursor.fetchone()[0]

        if not transportation_tags_exists:
            cursor.execute("""
                ALTER TABLE adventures_transportation
                ADD COLUMN tags VARCHAR(100)[] NULL;
            """)

        # Check if tags column exists on lodging
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'adventures_lodging'
                AND column_name = 'tags'
            );
        """)
        lodging_tags_exists = cursor.fetchone()[0]

        if not lodging_tags_exists:
            cursor.execute("""
                ALTER TABLE adventures_lodging
                ADD COLUMN tags VARCHAR(100)[] NULL;
            """)


def reverse_migration(apps, schema_editor):
    """Remove the columns (for rollback)."""
    with connection.cursor() as cursor:
        cursor.execute("ALTER TABLE adventures_transportation DROP COLUMN IF EXISTS tags;")
        cursor.execute("ALTER TABLE adventures_lodging DROP COLUMN IF EXISTS tags;")


class Migration(migrations.Migration):

    dependencies = [
        ('adventures', '0075_visit_transportation_lodging_safe'),
    ]

    operations = [
        migrations.RunPython(add_tags_columns_if_not_exist, reverse_migration),
    ]
