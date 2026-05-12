"""
One-off management command to delete civic_api races whose titles were saved
as 'Untitled Contest' (due to the old mapper missing the ballotTitle field)
and reset the parent elections' last_synced_at so they are re-synced on the
next scheduler run.

Usage:
    python manage.py reset_stale_races [--dry-run]
"""

from django.core.management.base import BaseCommand

from elections.models import Election, Race


class Command(BaseCommand):
    help = "Delete stale 'Untitled Contest' civic_api races and reset their elections for re-sync"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be deleted without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        stale_races = Race.objects.filter(office_title="Untitled Contest", source=Race.Source.CIVIC_API)
        count = stale_races.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No stale races found."))
            return

        election_ids = list(stale_races.values_list("election_id", flat=True).distinct())
        election_names = list(
            Election.objects.filter(pk__in=election_ids).values_list("name", flat=True)
        )

        self.stdout.write(f"Found {count} stale race(s) across {len(election_ids)} election(s):")
        for name in election_names:
            self.stdout.write(f"  - {name}")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — no changes made."))
            return

        stale_races.delete()
        Election.objects.filter(pk__in=election_ids).update(last_synced_at=None)

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {count} stale race(s) and reset {len(election_ids)} election(s) for re-sync."
            )
        )
