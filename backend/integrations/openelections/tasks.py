from __future__ import annotations

import datetime
import hashlib
import logging

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from elections.models import Race
from integrations.orchestrator.candidate_matcher import CandidateMatcher
from integrations.orchestrator.exceptions import AmbiguousMatchError, NoRaceFoundError
from integrations.orchestrator.race_matcher import RaceMatcher
from integrations.orchestrator.source_store import SourceRecordStore
from ops.models import SyncLog
from results.models import OfficialResult

from .client import OpenElectionsClient
from .mappers import map_result_row, parse_result_file_metadata

logger = logging.getLogger(__name__)


@shared_task
def check_openelections_new_results(state: str):
    state = (state or '').upper()
    sync_log = SyncLog.objects.create(
        source='openelections',
        task_name='check_openelections_new_results',
        address_label=state,
        status=SyncLog.Status.STARTED,
    )
    client = OpenElectionsClient()

    try:
        previous_sha = _last_processed_commit_sha(state)
        latest_sha = client.get_latest_commit_sha(state)
        if not latest_sha:
            sync_log.last_error = 'no repository commits found'
            sync_log.status = SyncLog.Status.COMPLETED_WITH_WARNINGS
            sync_log.error_count = 1
            sync_log.completed_at = timezone.now()
            sync_log.save(update_fields=['last_error', 'status', 'error_count', 'completed_at'])
            return {'queued': 0, 'state': state}

        if latest_sha == previous_sha:
            sync_log.last_error = 'no changes detected'
            sync_log.notes = _commit_note(latest_sha)
            sync_log.status = SyncLog.Status.COMPLETED
            sync_log.completed_at = timezone.now()
            sync_log.save(update_fields=['last_error', 'notes', 'status', 'completed_at'])
            return {'queued': 0, 'state': state, 'sha': latest_sha}

        files = client.list_result_files(state, since_sha=previous_sha)
        queued = 0
        for file_info in files:
            file_path = str(file_info.get('path') or '').strip()
            if not file_path:
                continue
            election_date, _ = parse_result_file_metadata(file_path)
            ingest_openelections_state.delay(state=state, file_path=file_path, election_date=election_date)
            queued += 1

        sync_log.records_created = queued
        sync_log.records_skipped = 0 if queued else 1
        sync_log.last_error = '' if queued else 'no new CSV files found'
        sync_log.notes = _commit_note(latest_sha)
        sync_log.status = SyncLog.Status.COMPLETED
        sync_log.completed_at = timezone.now()
        sync_log.save(
            update_fields=['records_created', 'records_skipped', 'last_error', 'notes', 'status', 'completed_at']
        )
        return {'queued': queued, 'state': state, 'sha': latest_sha}
    except Exception as exc:
        logger.exception('OpenElections scan failed for state=%s', state)
        sync_log.error_count = 1
        sync_log.last_error = str(exc)
        sync_log.status = SyncLog.Status.FAILED
        sync_log.completed_at = timezone.now()
        sync_log.save(update_fields=['error_count', 'last_error', 'status', 'completed_at'])
        raise


@shared_task
def ingest_openelections_state(state: str, file_path: str, election_date: str):
    state = (state or '').upper()
    cycle_year = int(str(election_date).split('-', 1)[0]) if election_date else None
    sync_log = SyncLog.objects.create(
        source='openelections',
        task_name='ingest_openelections_state',
        address_label=state,
        cycle_year=cycle_year,
        status=SyncLog.Status.STARTED,
    )
    client = OpenElectionsClient()
    store = SourceRecordStore()
    race_matcher = RaceMatcher()
    candidate_matcher = CandidateMatcher()
    created_count = 0
    updated_count = 0
    skipped_count = 0
    warning_count = 0
    last_warning = ''

    try:
        _, office = parse_result_file_metadata(file_path)
        file_info = _result_file_by_path(client, state, file_path)
        if file_info is None or not file_info.get('download_url'):
            raise ValueError(f'OpenElections file not found: {file_path}')

        for raw_row in client.download_csv(file_info['download_url']):
            mapped = map_result_row(raw_row, state, election_date, office)
            external_id = _source_record_external_id(file_path, raw_row)
            source_record, changed = store.upsert('openelections', external_id, raw_row)
            if not changed:
                skipped_count += 1
                continue
            if mapped is None:
                skipped_count += 1
                continue

            race_payload = {
                'office_title': _office_title(mapped['office']),
                'normalized_office_title': _normalize(mapped['office']),
                'election_date': mapped['election_date'],
                'state': mapped['state'],
                'district': mapped['district'] or '',
                'district_number': mapped['district'] or '',
                'jurisdiction': mapped['raw_county'] or state,
                'geography_scope': _geography_scope(mapped),
                'race_type': Race.RaceType.CANDIDATE,
                'source': 'openelections',
            }

            try:
                race, _ = race_matcher.find_or_create('openelections', external_id, race_payload)
            except (NoRaceFoundError, AmbiguousMatchError) as exc:
                warning_count += 1
                last_warning = str(exc)
                skipped_count += 1
                _save_source_links(source_record)
                continue

            candidate_payload = {
                'name': mapped['candidate_name'],
                'party': mapped['party'],
                'source_metadata': {
                    'openelections': {
                        'external_id': external_id,
                        'file_path': file_path,
                        'office': mapped['office'],
                        'election_date': mapped['election_date'],
                        'raw_county': mapped['raw_county'],
                        'raw_precinct': mapped['raw_precinct'],
                        'votes': mapped['votes'],
                        'winner': mapped['winner'],
                    }
                },
            }
            candidate, action = candidate_matcher.enrich(race, 'openelections', external_id, candidate_payload)
            if candidate is None or action == 'ambiguous':
                warning_count += 1
                last_warning = f'{action}:{external_id}'
                skipped_count += 1
                _save_source_links(source_record, race=race)
                continue
            if action == 'no_match':
                warning_count += 1
                last_warning = f'no_match:{external_id}'
                skipped_count += 1
                _save_source_links(source_record, race=race)
                continue

            result_lookup = {
                'race': race,
                'candidate': candidate,
                'measure_option': None,
                'round_number': 1,
                'jurisdiction_fragment': _jurisdiction_fragment(mapped),
            }
            result_exists = OfficialResult.objects.filter(**result_lookup).exists()
            with transaction.atomic():
                OfficialResult.objects.update_or_create(
                    **result_lookup,
                    defaults={
                        'vote_count': mapped['votes'] or 0,
                        'vote_pct': None,
                        'is_winner': mapped['winner'],
                        'result_type': OfficialResult.ResultType.OFFICIAL,
                        'is_write_in_aggregate': False,
                        'source_url': file_info['download_url'],
                        'raw_payload': raw_row,
                        'certified_at': _certified_at(mapped['election_date']),
                    },
                )
            if result_exists:
                updated_count += 1
            else:
                created_count += 1
            _save_source_links(source_record, race=race, candidate=candidate)

        sync_log.records_created = created_count
        sync_log.records_updated = updated_count
        sync_log.records_skipped = skipped_count
        sync_log.error_count = warning_count
        sync_log.last_error = last_warning
        sync_log.status = SyncLog.Status.COMPLETED_WITH_WARNINGS if warning_count else SyncLog.Status.COMPLETED
        sync_log.completed_at = timezone.now()
        sync_log.save(
            update_fields=[
                'records_created',
                'records_updated',
                'records_skipped',
                'error_count',
                'last_error',
                'status',
                'completed_at',
            ]
        )
        return {
            'created': created_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'warnings': warning_count,
            'state': state,
            'file_path': file_path,
        }
    except Exception as exc:
        logger.exception('OpenElections ingest failed for state=%s file=%s', state, file_path)
        sync_log.error_count += 1
        sync_log.last_error = str(exc)
        sync_log.status = SyncLog.Status.FAILED
        sync_log.completed_at = timezone.now()
        sync_log.save(update_fields=['error_count', 'last_error', 'status', 'completed_at'])
        raise


def _last_processed_commit_sha(state: str) -> str | None:
    sync_log = (
        SyncLog.objects.filter(
            source='openelections',
            task_name='check_openelections_new_results',
            address_label=state,
            status__in=[SyncLog.Status.COMPLETED, SyncLog.Status.COMPLETED_WITH_WARNINGS],
        )
        .exclude(notes='')
        .order_by('-started_at')
        .first()
    )
    if sync_log is None:
        return None
    note = sync_log.notes or ''
    prefix = 'last_processed_commit_sha='
    if note.startswith(prefix):
        return note[len(prefix):] or None
    return None


def _commit_note(sha: str) -> str:
    return f'last_processed_commit_sha={sha}'


def _result_file_by_path(client: OpenElectionsClient, state: str, file_path: str) -> dict | None:
    for file_info in client.list_result_files(state):
        if str(file_info.get('path') or '').strip() == file_path:
            return file_info
    return None


def _source_record_external_id(file_path: str, row: dict) -> str:
    parts = [
        file_path,
        str(row.get('county') or '').strip(),
        str(row.get('precinct') or '').strip(),
        str(row.get('office') or '').strip(),
        str(row.get('district') or '').strip(),
        str(row.get('party') or '').strip(),
        str(row.get('candidate') or '').strip(),
    ]
    return hashlib.sha256('::'.join(parts).encode()).hexdigest()


def _jurisdiction_fragment(mapped: dict) -> str:
    parts = [mapped.get('raw_county') or '', mapped.get('raw_precinct') or '']
    return ' / '.join([part for part in parts if part])


def _geography_scope(mapped: dict) -> str:
    if mapped.get('district'):
        return 'district'
    office = _normalize(mapped.get('office', ''))
    if office in {'president', 'u.s. senate', 'us senate', 'governor', 'attorney general'}:
        return 'statewide'
    return 'local' if mapped.get('raw_county') else 'statewide'


def _office_title(value: str) -> str:
    cleaned = ' '.join(str(value or '').replace('_', ' ').split())
    return cleaned.title() if cleaned else 'Office'


def _normalize(value: str) -> str:
    return ' '.join(str(value or '').strip().lower().replace('_', ' ').split())


def _certified_at(election_date: str):
    date_value = datetime.date.fromisoformat(str(election_date))
    current_tz = timezone.get_current_timezone()
    return timezone.make_aware(datetime.datetime.combine(date_value, datetime.time.min), current_tz)


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
