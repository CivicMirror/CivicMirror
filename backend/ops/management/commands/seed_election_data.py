"""
One-time seed command for cold-start deployments.

Runs all data-source adapters in dependency order so the database is populated
with live election data before Celery beat takes over for ongoing updates.

Run order (each step enriches the data from the previous one):
  1. Census/OCD   — district boundary records (standalone, no DB deps)
  2. Google Civic — elections + races + candidates (creates the canonical rows)
  3. Congress     — bioguide IDs + social links (enriches Civic candidates)
  4. FEC          — fec_candidate_id + finance links (enriches Civic candidates)
  5. Open States  — state legislator contact info  (opt-in, rate-limited)

Usage:
  python manage.py seed_election_data
  python manage.py seed_election_data --skip-fec --include-openstates
  python manage.py seed_election_data --only-step census
"""
import logging
import time

from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)

_STEPS = ['census', 'civic', 'congress', 'fec', 'openstates']


class Command(BaseCommand):
    help = (
        'Seed the database with live election data from all configured sources. '
        'Intended for a fresh deployment before Celery beat is active.'
    )

    def add_arguments(self, parser):
        skip_group = parser.add_argument_group('skip individual steps')
        skip_group.add_argument('--skip-census', action='store_true', help='Skip Census/OCD district refresh.')
        skip_group.add_argument('--skip-civic', action='store_true', help='Skip Google Civic API election+race sync.')
        skip_group.add_argument('--skip-congress', action='store_true', help='Skip Congress-legislators enrichment.')
        skip_group.add_argument('--skip-fec', action='store_true', help='Skip FEC candidate enrichment.')
        skip_group.add_argument(
            '--include-openstates',
            action='store_true',
            help=(
                'Include Open States legislator enrichment. Off by default because '
                'syncing all 50 states may exhaust the 500 req/day free-tier quota.'
            ),
        )
        parser.add_argument(
            '--only-step',
            choices=_STEPS,
            metavar='STEP',
            help=f'Run only one step and exit. One of: {", ".join(_STEPS)}',
        )

    def handle(self, *args, **options):
        self._check_database()
        self._configure_eager_celery()

        only = options.get('only_step')

        steps = [
            ('census', not options['skip_census'], self._seed_census),
            ('civic', not options['skip_civic'], self._seed_civic),
            ('congress', not options['skip_congress'], self._seed_congress),
            ('fec', not options['skip_fec'], self._seed_fec),
            ('openstates', options['include_openstates'], self._seed_openstates),
        ]

        if only:
            steps = [(name, True, fn) for name, _, fn in steps if name == only]

        self.stdout.write(self.style.MIGRATE_HEADING('\nCivicMirror election data seed\n'))

        any_ran = False
        for name, enabled, fn in steps:
            if not enabled:
                self.stdout.write(f'  [{name}] skipped')
                continue
            any_ran = True
            self._run_step(name, fn)

        if not any_ran:
            raise CommandError('All steps were skipped. Nothing to do.')

        self.stdout.write(self.style.SUCCESS('\nSeed complete. Celery beat will handle ongoing updates.\n'))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _check_database(self):
        """Fail fast if Django is pointed at SQLite — that means DATABASE_URL is missing."""
        from django.db import connection  # noqa: PLC0415
        if 'sqlite' in connection.vendor:
            raise CommandError(
                'DATABASE_URL is not configured — Django is using SQLite. '
                'Set DATABASE_URL in the environment before seeding.'
            )

    def _configure_eager_celery(self):
        """
        Force Celery into eager (synchronous) mode for the duration of this
        process so that tasks queued with .delay() run inline — e.g. the
        sync_election_races sub-tasks fired by sync_elections.

        Celery 5.x with Django settings integration ignores direct assignment
        to app.conf — we must mutate django.conf.settings so that Celery's
        lazy settings reader picks up the change.
        """
        try:
            from django.conf import settings as django_settings  # noqa: PLC0415
            django_settings.CELERY_TASK_ALWAYS_EAGER = True
            django_settings.CELERY_TASK_EAGER_PROPAGATES = True
        except Exception:
            self.stdout.write(
                self.style.WARNING(
                    '  [celery] Could not enable eager mode — tasks will be '
                    'queued normally (requires a running broker).'
                )
            )

    def _run_step(self, label: str, fn):
        self.stdout.write(f'  [{label}] starting...')
        t0 = time.monotonic()
        try:
            result = fn()
            elapsed = time.monotonic() - t0
            self.stdout.write(self.style.SUCCESS(f'  [{label}] done in {elapsed:.1f}s — {result}'))
        except Exception as exc:
            elapsed = time.monotonic() - t0
            self.stdout.write(self.style.ERROR(f'  [{label}] FAILED after {elapsed:.1f}s — {exc}'))
            logger.exception('Seed step [%s] failed', label)

    # ------------------------------------------------------------------
    # Step implementations
    # ------------------------------------------------------------------

    def _seed_census(self):
        from integrations.census.tasks import refresh_district_records  # noqa: PLC0415
        return refresh_district_records.apply().get()

    def _seed_civic(self):
        from integrations.civic.tasks import sync_elections  # noqa: PLC0415
        return sync_elections.apply().get()

    def _seed_congress(self):
        from integrations.congress.tasks import sync_congress_legislators  # noqa: PLC0415
        return sync_congress_legislators.apply().get()

    def _seed_fec(self):
        from integrations.fec.tasks import sync_fec_candidates  # noqa: PLC0415
        return sync_fec_candidates.apply().get()

    def _seed_openstates(self):
        """
        Sync Open States for all 50 states.

        The free tier allows 500 requests/day.  Seeding all states may use a
        significant portion of that budget.  The fan-out task already staggers
        requests with a 60 s countdown per state; in eager mode those countdowns
        are ignored, so all 50 states run back-to-back.
        """
        from integrations.openstates.tasks import sync_openstates_all_states  # noqa: PLC0415
        return sync_openstates_all_states.apply().get()
