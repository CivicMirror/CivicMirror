import logging

from celery import shared_task
from django.utils import timezone

from ops.models import SyncLog
from integrations.orchestrator.source_store import SourceRecordStore
from integrations.orchestrator.candidate_matcher import CandidateMatcher
from integrations.orchestrator.exceptions import AmbiguousMatchError

from .client import CongressLegislatorsClient
from .mappers import map_legislator

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=1)
def sync_congress_legislators(self):
    """
    Weekly task: download legislators-current.json (ETag-cached).
    If unchanged (fetch returns None), log 'no changes detected' and complete.

    For each legislator:
      1. SourceRecordStore.upsert('congress', bioguide_id, raw)
         — skip if unchanged
      2. map_legislator(raw)
         — skip if returns None (inactive)
      3. CandidateMatcher.enrich(
             race=None,      ← congress enrichment searches by state+office without a race
             source='congress',
             external_id=bioguide_id,
             enrichment_payload=mapped
         )
         Note: CandidateMatcher needs to handle race=None by doing cross-race
         matching on state + office_type + district instead of within-race matching.
         Log 'no_match' and 'ambiguous' to SyncLog.last_error as warnings (not failures).

    Log to SyncLog with source='congress', task_name='sync_congress_legislators'.
    """
    sync_log = SyncLog.objects.create(source='congress', task_name='sync_congress_legislators', status=SyncLog.Status.STARTED)
    client = CongressLegislatorsClient()
    store = SourceRecordStore()
    matcher = CandidateMatcher()
    updated_count = 0
    skipped_count = 0
    warnings: list[str] = []

    try:
        payloads, changed = client.fetch_current()
        if payloads is None and not changed:
            sync_log.last_error = 'no changes detected'
            sync_log.status = SyncLog.Status.COMPLETED
            sync_log.completed_at = timezone.now()
            sync_log.save(update_fields=['last_error', 'status', 'completed_at'])
            return {'updated': 0, 'skipped': 0, 'warnings': 0}

        for raw in payloads or []:
            bioguide_id = str(((raw.get('id') or {}).get('bioguide') or '')).strip()
            if not bioguide_id:
                skipped_count += 1
                warnings.append('missing bioguide_id')
                continue

            _, source_changed = store.upsert('congress', bioguide_id, raw)
            if not source_changed:
                skipped_count += 1
                continue

            mapped = map_legislator(raw)
            if mapped is None:
                skipped_count += 1
                continue

            try:
                _, action = matcher.enrich(
                    race=None,
                    source='congress',
                    external_id=bioguide_id,
                    enrichment_payload=mapped,
                )
            except AmbiguousMatchError:
                action = 'ambiguous'

            if action == 'enriched':
                updated_count += 1
                continue
            if action == 'skipped':
                skipped_count += 1
                continue
            if action in {'no_match', 'ambiguous'}:
                skipped_count += 1
                warnings.append(f'{action}:{bioguide_id}')
                continue
            skipped_count += 1

        sync_log.records_updated = updated_count
        sync_log.records_skipped = skipped_count
        sync_log.error_count = len(warnings)
        if warnings:
            sync_log.last_error = '\n'.join(warnings)
            sync_log.status = SyncLog.Status.COMPLETED_WITH_WARNINGS
        else:
            sync_log.status = SyncLog.Status.COMPLETED
        sync_log.completed_at = timezone.now()
        sync_log.save(
            update_fields=['records_updated', 'records_skipped', 'error_count', 'last_error', 'status', 'completed_at']
        )
        return {'updated': updated_count, 'skipped': skipped_count, 'warnings': len(warnings)}
    except Exception as exc:
        logger.exception('Congress legislators sync failed')
        sync_log.error_count += 1
        sync_log.last_error = str(exc)
        sync_log.status = SyncLog.Status.FAILED
        sync_log.completed_at = timezone.now()
        sync_log.save(update_fields=['error_count', 'last_error', 'status', 'completed_at'])
        raise
