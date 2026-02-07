# Migration to convert Transportation and Lodging from ForeignKey to ManyToMany for collections
# This migration:
# 1. Creates the M2M tables
# 2. Migrates existing data from FK to M2M
# 3. Removes the old FK columns

from django.db import migrations, connection


def migrate_fk_to_m2m(apps, schema_editor):
    """Migrate existing FK relationships to M2M."""
    with connection.cursor() as cursor:
        # Create M2M table for Transportation if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adventures_transportation_collections (
                id BIGSERIAL PRIMARY KEY,
                transportation_id UUID NOT NULL REFERENCES adventures_transportation(id) ON DELETE CASCADE,
                collection_id UUID NOT NULL REFERENCES adventures_collection(id) ON DELETE CASCADE,
                UNIQUE (transportation_id, collection_id)
            );
        """)

        # Create M2M table for Lodging if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adventures_lodging_collections (
                id BIGSERIAL PRIMARY KEY,
                lodging_id UUID NOT NULL REFERENCES adventures_lodging(id) ON DELETE CASCADE,
                collection_id UUID NOT NULL REFERENCES adventures_collection(id) ON DELETE CASCADE,
                UNIQUE (lodging_id, collection_id)
            );
        """)

        # Check if collection_id column exists on transportation
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'adventures_transportation'
                AND column_name = 'collection_id'
            );
        """)
        transportation_fk_exists = cursor.fetchone()[0]

        # Migrate Transportation FK data to M2M
        if transportation_fk_exists:
            cursor.execute("""
                INSERT INTO adventures_transportation_collections (transportation_id, collection_id)
                SELECT id, collection_id
                FROM adventures_transportation
                WHERE collection_id IS NOT NULL
                ON CONFLICT DO NOTHING;
            """)

            # Drop the old FK column
            cursor.execute("""
                ALTER TABLE adventures_transportation DROP COLUMN IF EXISTS collection_id;
            """)

        # Check if collection_id column exists on lodging
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = 'adventures_lodging'
                AND column_name = 'collection_id'
            );
        """)
        lodging_fk_exists = cursor.fetchone()[0]

        # Migrate Lodging FK data to M2M
        if lodging_fk_exists:
            cursor.execute("""
                INSERT INTO adventures_lodging_collections (lodging_id, collection_id)
                SELECT id, collection_id
                FROM adventures_lodging
                WHERE collection_id IS NOT NULL
                ON CONFLICT DO NOTHING;
            """)

            # Drop the old FK column
            cursor.execute("""
                ALTER TABLE adventures_lodging DROP COLUMN IF EXISTS collection_id;
            """)


def reverse_migration(apps, schema_editor):
    """Reverse the migration (convert M2M back to FK)."""
    with connection.cursor() as cursor:
        # Add back FK columns
        cursor.execute("""
            ALTER TABLE adventures_transportation
            ADD COLUMN IF NOT EXISTS collection_id UUID REFERENCES adventures_collection(id) ON DELETE CASCADE;
        """)
        cursor.execute("""
            ALTER TABLE adventures_lodging
            ADD COLUMN IF NOT EXISTS collection_id UUID REFERENCES adventures_collection(id) ON DELETE CASCADE;
        """)

        # Migrate first collection from M2M back to FK (only one can be stored)
        cursor.execute("""
            UPDATE adventures_transportation t
            SET collection_id = (
                SELECT collection_id FROM adventures_transportation_collections
                WHERE transportation_id = t.id
                LIMIT 1
            );
        """)
        cursor.execute("""
            UPDATE adventures_lodging l
            SET collection_id = (
                SELECT collection_id FROM adventures_lodging_collections
                WHERE lodging_id = l.id
                LIMIT 1
            );
        """)

        # Drop M2M tables
        cursor.execute("DROP TABLE IF EXISTS adventures_transportation_collections;")
        cursor.execute("DROP TABLE IF EXISTS adventures_lodging_collections;")


class Migration(migrations.Migration):

    dependencies = [
        ('adventures', '0078_add_tags_transportation_lodging'),
    ]

    operations = [
        migrations.RunPython(migrate_fk_to_m2m, reverse_migration),
    ]
