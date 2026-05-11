from __future__ import annotations

import datetime
import logging

from celery import shared_task
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=12, default_retry_delay=3600)
def ingest_official_results(self, state: str, election_id: int):
    """
    Fetch and upsert official results for all races in the given election.
    Retries hourly; gives up after 12 attempts (12 hours post-trigger).
    """
    from elections.models import Election, Race
    from results.adapters.registry import get_adapter

    adapter_class = get_adapter(state)
    if not adapter_class:
        logger.warning('No adapter for state %s; skipping', state)
        return

    try:
        election = Election.objects.get(pk=election_id)
    except Election.DoesNotExist:
        logger.error('Election %s not found', election_id)
        return

    adapter = adapter_class()
    try:
        result = adapter.fetch_results(election.election_date, election_id)
    except Exception as exc:
        logger.exception('Adapter fetch failed for %s/%s', state, election_id)
        raise self.retry(exc=exc)

    if not result.rows:
        certification_status = (
            Race.CertificationStatus.PARTIAL_RESULTS
            if result.mapping_confidence in {'none', 'partial'}
            else Race.CertificationStatus.RESULTS_PENDING
        )
        Race.objects.filter(election=election).update(certification_status=certification_status)
        return

    races = {
        race.id: race
        for race in Race.objects.filter(election=election).select_related('election')
    }

    for race in races.values():
        _process_race_results(race, result, state)


def _process_race_results(race, adapter_result, state):
    from elections.models import Candidate, MeasureOption, Race
    from results.models import OfficialResult

    matched_rows = []
    any_partial = False

    for row in adapter_result.rows:
        candidate = None
        measure_option = None

        if row.is_write_in_aggregate:
            if race.race_type != Race.RaceType.CANDIDATE:
                continue
        elif row.candidate_name:
            if race.race_type != Race.RaceType.CANDIDATE:
                continue
            candidate = (
                Candidate.objects.filter(race=race, name=row.candidate_name).first()
                or Candidate.objects.filter(race=race, name__iexact=row.candidate_name).first()
            )
            if not candidate:
                logger.warning("No candidate match for '%s' in race %s (%s)", row.candidate_name, race.id, state)
                any_partial = True
                continue
        elif row.option_label:
            if race.race_type != Race.RaceType.MEASURE:
                continue
            measure_option = (
                MeasureOption.objects.filter(race=race, option_label=row.option_label).first()
                or MeasureOption.objects.filter(race=race, option_label__iexact=row.option_label).first()
            )
            if not measure_option:
                logger.warning("No measure option match for '%s' in race %s (%s)", row.option_label, race.id, state)
                any_partial = True
                continue
        else:
            any_partial = True
            continue

        with transaction.atomic():
            OfficialResult.objects.update_or_create(
                race=race,
                candidate=candidate,
                measure_option=measure_option,
                round_number=row.round_number,
                jurisdiction_fragment=row.jurisdiction_fragment,
                defaults={
                    'vote_count': row.vote_count,
                    'vote_pct': row.vote_pct,
                    'is_winner': row.is_winner,
                    'result_type': row.result_type,
                    'is_write_in_aggregate': row.is_write_in_aggregate,
                    'source_url': adapter_result.source_url,
                    'raw_payload': row.raw,
                    'certified_at': _certified_at_for_row(race, row.result_type),
                },
            )
        matched_rows.append(row)

    if adapter_result.mapping_confidence == 'full' and not any_partial and matched_rows:
        race.certification_status = Race.CertificationStatus.RESULTS_CERTIFIED
        race.race_status = Race.RaceStatus.ARCHIVED
        race.save(update_fields=['certification_status', 'race_status'])
        return

    race.certification_status = Race.CertificationStatus.PARTIAL_RESULTS
    race.save(update_fields=['certification_status'])


def _certified_at_for_row(race, result_type: str):
    from results.models import OfficialResult

    if result_type != OfficialResult.ResultType.OFFICIAL:
        return None
    election_date = race.election.election_date
    if isinstance(election_date, str):
        election_date = datetime.date.fromisoformat(election_date)
    current_tz = timezone.get_current_timezone()
    return timezone.make_aware(datetime.datetime.combine(election_date, datetime.time.min), current_tz)
