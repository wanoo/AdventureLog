"""
Management command to merge duplicate categories.

In collaborative mode, categories should be unique by name.
This command merges all categories with the same name into a single global category.
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from adventures.models import Category, Location


class Command(BaseCommand):
    help = 'Merge duplicate categories into single global categories'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))

        # Find all category names that have duplicates
        duplicate_names = (
            Category.objects.values('name')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
            .values_list('name', flat=True)
        )

        self.stdout.write(f'Found {len(duplicate_names)} category names with duplicates')

        total_merged = 0
        total_locations_updated = 0

        for name in duplicate_names:
            categories = Category.objects.filter(name=name).order_by('id')
            count = categories.count()

            self.stdout.write(f'\nProcessing "{name}" ({count} duplicates):')

            # Find or create the global category (prefer existing global one)
            global_cat = categories.filter(is_global=True).first()

            if not global_cat:
                # Use the first one and make it global
                global_cat = categories.first()
                if not dry_run:
                    global_cat.is_global = True
                    global_cat.save()
                self.stdout.write(f'  - Made category {global_cat.id} global')

            # Get all other categories to merge
            other_cats = categories.exclude(id=global_cat.id)

            for cat in other_cats:
                # Count locations using this category
                locations = Location.objects.filter(category=cat)
                loc_count = locations.count()

                self.stdout.write(f'  - Merging {cat.id} (user={cat.user}, {loc_count} locations) into {global_cat.id}')

                if not dry_run:
                    # Update all locations to use the global category
                    locations.update(category=global_cat)
                    total_locations_updated += loc_count

                    # Delete the duplicate category
                    cat.delete()
                    total_merged += 1

        self.stdout.write('')
        if dry_run:
            self.stdout.write(self.style.WARNING(f'Would merge {total_merged} duplicate categories'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Merged {total_merged} duplicate categories'))
            self.stdout.write(self.style.SUCCESS(f'Updated {total_locations_updated} locations'))

        # Also ensure "general" category exists and is global
        general = Category.objects.filter(name='general').first()
        if general and not general.is_global:
            if not dry_run:
                general.is_global = True
                general.save()
            self.stdout.write(self.style.SUCCESS('Made "general" category global'))
        elif not general:
            if not dry_run:
                Category.objects.create(
                    name='general',
                    display_name='General',
                    icon='🌍',
                    is_global=True,
                    user=None
                )
            self.stdout.write(self.style.SUCCESS('Created global "general" category'))
