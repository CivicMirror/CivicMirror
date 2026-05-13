import logging
from datetime import timedelta

from celery import shared_task
from django.core.cache import cache
from django.utils import timezone

from elections.models import DistrictRecord
from ops.models import SyncLog

from .ocd_loader import load_ocd_divisions

logger = logging.getLogger(__name__)


@shared_task
def refresh_district_records():
    """
    Monthly task: refresh OCD division cache and update any stale DistrictRecords.
    Log to SyncLog with source='census'.
    """
    sync_log = SyncLog.objects.create(source='census', task_name='refresh_district_records', status=SyncLog.Status.STARTED)

    try:
        cache.delete('census:ocd_divisions')
        divisions = load_ocd_divisions()
        if not divisions:
            raise RuntimeError('Unable to refresh OCD divisions from the upstream CSV.')

        names_by_id = {division['id']: division['name'] for division in divisions}
        stale_before = timezone.now() - timedelta(days=30)
        updated_count = 0
        skipped_count = 0

        for record in DistrictRecord.objects.all():
            fields_to_update = []
            latest_name = names_by_id.get(record.ocd_division_id)
            if latest_name and latest_name != record.name:
                record.name = latest_name
                fields_to_update.append('name')

            if record.last_updated <= stale_before or fields_to_update:
                fields_to_update.append('last_updated')
                record.save(update_fields=fields_to_update)
                updated_count += 1
            else:
                skipped_count += 1

        sync_log.records_updated = updated_count
        sync_log.records_skipped = skipped_count
        sync_log.status = SyncLog.Status.COMPLETED
        sync_log.completed_at = timezone.now()
        sync_log.save(update_fields=['records_updated', 'records_skipped', 'status', 'completed_at'])
        return {'divisions': len(divisions), 'updated': updated_count, 'skipped': skipped_count}
    except Exception as exc:
        logger.exception('Census district refresh failed')
        sync_log.error_count = 1
        sync_log.last_error = str(exc)
        sync_log.status = SyncLog.Status.FAILED
        sync_log.completed_at = timezone.now()
        sync_log.save(update_fields=['error_count', 'last_error', 'status', 'completed_at'])
        raise
