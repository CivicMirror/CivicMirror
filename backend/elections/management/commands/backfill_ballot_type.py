"""
Management command to backfill the ballot_type field on existing civic_api races.

Races imported before the ballot_type mapper was added have ballot_type=''.
This command resets last_synced_at on their parent elections so the next
sync_elections run will re-pull and populate ballot_type via update_or_create.

Usage:
    python manage.py backfill_ballot_type [--dry-run] [--trigger-sync]
"""

from django.core.management.base import BaseCommand

from elections.models import Election, Race


class Command(BaseCommand):
    help = "Reset elections for re-sync to backfill ballot_type on existing civic_api races"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would change without making changes",
        )
        parser.add_argument(
            "--trigger-sync",
            action="store_true",
            help="Also run sync_elections synchronously after resetting freshness",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        trigger_sync = options["trigger_sync"]

        empty_races = Race.objects.filter(source=Race.Source.CIVIC_API, ballot_type="")
        count = empty_races.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("All civic_api races already have ballot_type set."))
            return

        election_ids = list(empty_races.values_list("election_id", flat=True).distinct())
        elections = list(Election.objects.filter(pk__in=election_ids))

        self.stdout.write(
            f"Found {count} civic_api race(s) with empty ballot_type across {len(elections)} election(s):"
        )
        for election in elections:
            self.stdout.write(f"  - [{election.pk}] {election.name} (source_id={election.source_id})")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — no changes made."))
            return

        Election.objects.filter(pk__in=election_ids).update(last_synced_at=None)
        self.stdout.write(
            self.style.SUCCESS(
                f"Reset last_synced_at on {len(election_ids)} election(s). "
                "They will be re-synced on the next scheduler run."
            )
        )

        if trigger_sync:
            from integrations.civic.addresses import REPRESENTATIVE_ADDRESSES  # noqa: PLC0415
            from integrations.civic.tasks import sync_election_races  # noqa: PLC0415

            _NATIONAL_SAMPLE_STATES = ["CA", "TX", "NY", "FL", "PA", "OH", "GA", "NC", "MI", "VA"]

            total_created = 0
            total_updated = 0
            for election in elections:
                if election.state and election.state in REPRESENTATIVE_ADDRESSES:
                    addrs = REPRESENTATIVE_ADDRESSES[election.state]
                else:
                    addrs = [
                        addr
                        for state in _NATIONAL_SAMPLE_STATES
                        for addr in REPRESENTATIVE_ADDRESSES.get(state, [])[:1]
                    ]
                for addr in addrs:
                    self.stdout.write(
                        f"  Syncing [{election.pk}] {election.name} via {addr['label']}..."
                    )
                    result = sync_election_races.apply(
                        args=[election.pk, addr['address'], addr['label']]
                    ).get()
                    total_created += result.get('created', 0)
                    total_updated += result.get('updated', 0)
                    self.stdout.write(
                        f"    created={result.get('created', 0)} updated={result.get('updated', 0)}"
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Sync complete: total created={total_created} updated={total_updated}"
                )
            )
