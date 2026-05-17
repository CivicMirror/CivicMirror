"""
One-off management command to remove the Google VIP test election (source_id=2000)
and all races attached to it from the database.

The VIP test election has an empty ocdDivisionId, which causes it to be stored as
jurisdiction_level='national'. Its test fixture races (LA city/county measures) then
appear in the national scope feed. The sync task now skips this election, but any
data already imported must be removed manually with this command.

Usage:
    python manage.py cleanup_vip_election [--dry-run]
"""

from django.core.management.base import BaseCommand

from elections.models import Election, Race

VIP_SOURCE_ID = "2000"


class Command(BaseCommand):
    help = "Remove the Google VIP test election (source_id=2000) and its races"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be deleted without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        try:
            election = Election.objects.get(source_id=VIP_SOURCE_ID)
        except Election.DoesNotExist:
            self.stdout.write(self.style.SUCCESS("VIP test election not found — nothing to do."))
            return

        race_count = Race.objects.filter(election=election).count()

        self.stdout.write(f"VIP test election: {election.name!r} (id={election.id})")
        self.stdout.write(f"  Races to delete: {race_count}")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — no changes made."))
            return

        Race.objects.filter(election=election).delete()
        election.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {race_count} race(s) and the VIP test election."
            )
        )
