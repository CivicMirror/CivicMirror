import logging
from datetime import date

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from integrations.census.resolver import resolve_ocd_id
from integrations.orchestrator.candidate_matcher import CandidateMatcher
from integrations.orchestrator.exceptions import AmbiguousMatchError, NoRaceFoundError
from integrations.orchestrator.race_matcher import RaceMatcher
from integrations.orchestrator.source_store import SourceRecordStore
from ops.models import SourceRecord, SyncLog

from .client import FECAPIForbidden, FECAPIRateLimitError, FECClient
from .mappers import current_cycle, fec_office_to_ocd_type, map_candidate

logger = logging.getLogger(__name__)

US_STATES = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA',
    'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT',
    'VA', 'WA', 'WV', 'WI', 'WY',
]


def _federal_general_election_date(cycle_year: int) -> date:
    for day in range(2, 9):
        candidate_date = date(cycle_year, 11, day)
        if candidate_date.weekday() == 1:
            return candidate_date
    return date(cycle_year, 11, 5)


def _office_runs():
    for office in ('H', 'S'):
        for state in US_STATES:
            yield office, state
    yield 'P', None


def _office_title(mapped_candidate: dict) -> str:
    office_full = ((mapped_candidate.get('source_metadata') or {}).get('fec') or {}).get('office_full') or ''
    if office_full:
        return str(office_full).strip()
    return {
        'H': 'U.S. House',
        'S': 'U.S. Senate',
        'P': 'President',
    }.get(mapped_candidate.get('office_type'), 'Federal Office')


def _geography_scope(office_type: str) -> str:
    ocd_type = fec_office_to_ocd_type(office_type)
    if ocd_type == 'cd':
        return 'district'
    if ocd_type == 's':
        return 'statewide'
    return 'federal'


def _source_record_exists(external_id: str) -> bool:
    return SourceRecord.objects.filter(source='fec', external_id=str(external_id)).exists()


def _save_source_links(source_record, *, race=None, candidate=None):
    fields_to_update = []
    current_race_id = getattr(source_record, 'linked_race_id', None)
    desired_race_id = getattr(race, 'pk', None)
    if current_race_id != desired_race_id:
        source_record.linked_race = race
        fields_to_update.append('linked_race')

    current_candidate_id = getattr(source_record, 'linked_candidate_id', None)
    desired_candidate_id = getattr(candidate, 'pk', None)
    if current_candidate_id != desired_candidate_id:
        source_record.linked_candidate = candidate
        fields_to_update.append('linked_candidate')

    if fields_to_update:
        source_record.save(update_fields=fields_to_update)


@shared_task(bind=True, max_retries=3)
def sync_fec_candidates(self, cycle_year: int | None = None):
    """
    Sync FEC candidates for House and Senate for each state, plus President nationally.
    cycle_year defaults to current_cycle().

    For each candidate:
      1. SourceRecordStore.upsert() — skip if unchanged
      2. map_candidate()
      3. resolve_ocd_id() for district
      4. RaceMatcher.find_or_create() — if NoRaceFoundError, skip (FEC is enrichment-only)
      5. CandidateMatcher.enrich()
      6. Link SourceRecord to matched Race/Candidate

    Log to SyncLog with source='fec', cycle_year=cycle_year.
    Handle FECAPIForbidden → FAILED status (no retry).
    Handle FECAPIRateLimitError → retry with 300s countdown.
    """
    cycle_year = cycle_year or current_cycle()
    sync_log = SyncLog.objects.create(
        source='fec',
        task_name='sync_fec_candidates',
        status=SyncLog.Status.STARTED,
        cycle_year=cycle_year,
    )
    client = FECClient()
    source_store = SourceRecordStore()
    race_matcher = RaceMatcher()
    candidate_matcher = CandidateMatcher()
    created_count = 0
    updated_count = 0
    skipped_count = 0
    election_date = _federal_general_election_date(cycle_year)

    try:
        for office, state in _office_runs():
            for raw_candidate in client.list_candidates_all_pages(office=office, state=state, cycle=cycle_year):
                external_id = str(raw_candidate.get('candidate_id') or '').strip()
                if not external_id:
                    skipped_count += 1
                    continue

                record_exists = _source_record_exists(external_id)
                source_record, changed = source_store.upsert('fec', external_id, raw_candidate)
                if not changed:
                    skipped_count += 1
                    continue

                if record_exists:
                    updated_count += 1
                else:
                    created_count += 1

                mapped_candidate = map_candidate(raw_candidate)
                if mapped_candidate is None:
                    skipped_count += 1
                    _save_source_links(source_record)
                    continue

                district_record = resolve_ocd_id(
                    mapped_candidate.get('state') or 'US',
                    mapped_candidate.get('office_type', ''),
                    mapped_candidate.get('district') or '',
                )
                district_records = [district_record] if district_record is not None else []
                race_payload = {
                    'ocd_division_id': district_record.ocd_division_id if district_record else '',
                    'normalized_office_title': mapped_candidate.get('normalized_office_title', ''),
                    'office_title': _office_title(mapped_candidate),
                    'election_date': election_date,
                    'state': mapped_candidate.get('state') or '',
                    'jurisdiction': district_record.name if district_record else (mapped_candidate.get('state') or 'United States'),
                    'geography_scope': _geography_scope(mapped_candidate.get('office_type', '')),
                    'race_type': 'candidate',
                    'district': mapped_candidate.get('district') or '',
                    'district_number': mapped_candidate.get('district') or '',
                    'source': 'fec',
                }

                try:
                    race, _ = race_matcher.find_or_create(
                        'fec',
                        external_id,
                        race_payload,
                        district_records=district_records,
                    )
                except (NoRaceFoundError, AmbiguousMatchError):
                    skipped_count += 1
                    _save_source_links(source_record)
                    continue

                candidate_payload = dict(mapped_candidate)
                candidate_payload['name'] = (((mapped_candidate.get('source_metadata') or {}).get('fec') or {}).get('name') or '').strip()
                candidate_payload['source_metadata'] = dict(((mapped_candidate.get('source_metadata') or {}).get('fec') or {}))
                candidate, action = candidate_matcher.enrich(race, 'fec', external_id, candidate_payload)
                if action != 'enriched':
                    skipped_count += 1
                _save_source_links(source_record, race=race, candidate=candidate)

        sync_log.records_created = created_count
        sync_log.records_updated = updated_count
        sync_log.records_skipped = skipped_count
        sync_log.status = SyncLog.Status.COMPLETED if sync_log.error_count == 0 else SyncLog.Status.COMPLETED_WITH_WARNINGS
        sync_log.completed_at = timezone.now()
        sync_log.save(update_fields=['records_created', 'records_updated', 'records_skipped', 'status', 'completed_at'])
        return {'created': created_count, 'updated': updated_count, 'skipped': skipped_count}
    except FECAPIForbidden as exc:
        sync_log.error_count = 1
        sync_log.last_error = str(exc)
        sync_log.status = SyncLog.Status.FAILED
        sync_log.completed_at = timezone.now()
        sync_log.save(update_fields=['error_count', 'last_error', 'status', 'completed_at'])
        raise
    except FECAPIRateLimitError as exc:
        sync_log.error_count = 1
        sync_log.last_error = str(exc)
        sync_log.status = SyncLog.Status.COMPLETED_WITH_WARNINGS
        sync_log.completed_at = timezone.now()
        sync_log.save(update_fields=['error_count', 'last_error', 'status', 'completed_at'])
        raise self.retry(exc=exc, countdown=getattr(settings, 'FEC_RATE_LIMIT_RETRY_SECONDS', 300))
    except Exception as exc:
        logger.exception('Unexpected FEC sync failure for cycle=%s', cycle_year)
        sync_log.error_count = 1
        sync_log.last_error = str(exc)
        sync_log.status = SyncLog.Status.FAILED
        sync_log.completed_at = timezone.now()
        sync_log.save(update_fields=['error_count', 'last_error', 'status', 'completed_at'])
        raise
