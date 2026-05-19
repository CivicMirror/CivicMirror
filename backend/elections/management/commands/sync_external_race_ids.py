"""Management command: sync_external_race_ids

Fetches races from the CivicMirror-API (civicmirror-worker) and populates the
``external_race_id`` field on local ``Race`` rows by matching on the combination
of ``office_title``, ``election_date``, and ``jurisdiction``.

Usage::

    python manage.py sync_external_race_ids

Environment variables:
    CIVIC_API_URL   Base URL of the CivicMirror-API (required)
    CIVIC_API_KEY   API key sent in the ``X-Api-Key`` header (required)
"""

import logging
import os
from urllib.parse import urljoin

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from elections.models import Race

logger = logging.getLogger(__name__)


def _build_match_key(office_title: str, election_date: str, jurisdiction: str) -> str:
    """Return a normalised composite key used to match local vs. remote races."""
    return (
        f"{' '.join(office_title.strip().lower().split())}"
        f"|{election_date}"
        f"|{' '.join(jurisdiction.strip().lower().split())}"
    )


def _fetch_all_races(base_url: str, api_key: str) -> list[dict]:
    """Page through /api/v1/races/ and return every race object."""
    races: list[dict] = []
    url = urljoin(base_url.rstrip("/") + "/", "api/v1/races/?page_size=200")
    headers = {"X-Api-Key": api_key}

    while url:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        payload = response.json()
        races.extend(payload.get("results", []))
        url = payload.get("next")

    return races


class Command(BaseCommand):
    help = (
        "Populate Race.external_race_id by matching local races against the "
        "CivicMirror-API on (office_title, election_date, jurisdiction)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print matches without writing to the database.",
        )
        parser.add_argument(
            "--api-url",
            default=os.environ.get("CIVIC_API_URL", ""),
            help="CivicMirror-API base URL (overrides CIVIC_API_URL env var).",
        )
        parser.add_argument(
            "--api-key",
            default=os.environ.get("CIVIC_API_KEY", ""),
            help="API key for X-Api-Key header (overrides CIVIC_API_KEY env var).",
        )

    def handle(self, *args, **options):
        api_url: str = options["api_url"]
        api_key: str = options["api_key"]
        dry_run: bool = options["dry_run"]

        if not api_url:
            raise CommandError("CIVIC_API_URL is not set. Pass --api-url or set the env var.")
        if not api_key:
            raise CommandError("CIVIC_API_KEY is not set. Pass --api-key or set the env var.")

        self.stdout.write("Fetching races from CivicMirror-API…")
        try:
            remote_races = _fetch_all_races(api_url, api_key)
        except requests.RequestException as exc:
            raise CommandError(f"Failed to fetch remote races: {exc}") from exc

        self.stdout.write(f"  Retrieved {len(remote_races)} remote races.")

        # Build a lookup: match_key → remote race id
        remote_by_key: dict[str, int] = {}
        for remote_race in remote_races:
            election = remote_race.get("election") or {}
            election_date = (
                election.get("election_date", "") if isinstance(election, dict) else ""
            )
            key = _build_match_key(
                remote_race.get("office_title", ""),
                election_date,
                remote_race.get("jurisdiction", ""),
            )
            if key in remote_by_key:
                logger.warning("Duplicate remote key: %s (ids %s and %s)", key, remote_by_key[key], remote_race["id"])
            else:
                remote_by_key[key] = remote_race["id"]

        # Load all local races with their election date
        local_races = Race.objects.select_related("election").filter(
            source__in=[Race.Source.CIVIC_API, Race.Source.OPENELECTIONS, Race.Source.MEDSL]
        )

        matched = 0
        unmatched = 0
        updates: list[Race] = []

        for local_race in local_races:
            key = _build_match_key(
                local_race.office_title,
                str(local_race.election.election_date),
                local_race.jurisdiction,
            )
            remote_id = remote_by_key.get(key)
            if remote_id is not None:
                if local_race.external_race_id != remote_id:
                    local_race.external_race_id = remote_id
                    updates.append(local_race)
                matched += 1
            else:
                unmatched += 1
                logger.debug("No remote match for local race %s (key: %s)", local_race.pk, key)

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] Would update {len(updates)} race(s). "
                    f"Matched: {matched}, Unmatched: {unmatched}."
                )
            )
            return

        with transaction.atomic():
            if updates:
                Race.objects.bulk_update(updates, ["external_race_id"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Updated {len(updates)} race(s). "
                f"Matched: {matched}, Unmatched: {unmatched}."
            )
        )
