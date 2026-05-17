import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from elections.models import Candidate, Election, MeasureOption, Race
from ops.models import SyncLog

from .addresses import REPRESENTATIVE_ADDRESSES
from .cache import get_cached_voter_info, races_are_fresh, set_cached_voter_info
from .client import CivicAPIClient, CivicAPIForbidden, CivicAPIRetryableError
from .mappers import map_candidate_defaults, map_contest_to_race_defaults, map_election_payload, measure_option_labels

logger = logging.getLogger(__name__)



def _backoff(retry_count: int) -> int:
    base = max(1, int(getattr(settings, 'CIVIC_RETRY_BACKOFF_SECONDS', 1)))
    return base * (2 ** retry_count)



_NATIONAL_SAMPLE_STATES = ["CA", "TX", "NY", "FL", "PA", "OH", "GA", "NC", "MI", "VA"]

# Google's documented VIP test election ID — never real data, always LA test fixtures.
_VIP_TEST_ELECTION_ID = "2000"


def _representative_addresses_for_election(election: Election) -> list[dict]:
    if election.state and election.state in REPRESENTATIVE_ADDRESSES:
        return REPRESENTATIVE_ADDRESSES[election.state]
    # For national/unknown elections sample a fixed set of large states to
    # avoid exhausting API quota by querying all 50 states.
    return [
        addr
        for state in _NATIONAL_SAMPLE_STATES
        for addr in REPRESENTATIVE_ADDRESSES.get(state, [])[:1]
    ]


@shared_task(bind=True, max_retries=3)
def sync_elections(self):
    sync_log = SyncLog.objects.create(source='civic_api', task_name='sync_elections', status=SyncLog.Status.STARTED)
    client = CivicAPIClient()
    created_count = 0
    updated_count = 0
    queued_count = 0

    try:
        for payload in client.list_elections():
            if str(payload.get("source_id")) == _VIP_TEST_ELECTION_ID:
                logger.debug("Skipping VIP test election (source_id=%s)", _VIP_TEST_ELECTION_ID)
                continue
            mapped = map_election_payload(payload)
            source_id = mapped.pop('source_id')
            election, created = Election.objects.update_or_create(source_id=source_id, defaults=mapped)
            created_count += int(created)
            updated_count += int(not created)
            if not races_are_fresh(election):
                for address in _representative_addresses_for_election(election):
                    sync_election_races.delay(election.id, address['address'], address['label'])
                    queued_count += 1
        sync_log.records_created = created_count
        sync_log.records_updated = updated_count
        sync_log.status = SyncLog.Status.COMPLETED
        sync_log.completed_at = timezone.now()
        sync_log.save(update_fields=['records_created', 'records_updated', 'status', 'completed_at'])
        return {'created': created_count, 'updated': updated_count, 'queued': queued_count}
    except CivicAPIForbidden as exc:
        sync_log.error_count = 1
        sync_log.last_error = str(exc)
        sync_log.status = SyncLog.Status.FAILED
        sync_log.completed_at = timezone.now()
        sync_log.save(update_fields=['error_count', 'last_error', 'status', 'completed_at'])
        raise
    except CivicAPIRetryableError as exc:
        sync_log.error_count = 1
        sync_log.last_error = str(exc)
        sync_log.status = SyncLog.Status.COMPLETED_WITH_WARNINGS
        sync_log.completed_at = timezone.now()
        sync_log.save(update_fields=['error_count', 'last_error', 'status', 'completed_at'])
        raise self.retry(exc=exc, countdown=_backoff(self.request.retries))


@shared_task(bind=True, max_retries=3)
def sync_election_races(self, election_id: int, address: str, address_label: str):
    election = Election.objects.get(pk=election_id)
    sync_log = SyncLog.objects.create(
        election=election,
        source='civic_api',
        task_name='sync_election_races',
        address_label=address_label,
        status=SyncLog.Status.STARTED,
    )
    client = CivicAPIClient()
    created_count = 0
    updated_count = 0

    try:
        payload = get_cached_voter_info(address, election.source_id)
        if payload is None:
            payload = client.get_voter_info(address, election.source_id)
            if payload:
                set_cached_voter_info(address, election.source_id, payload)

        contests = payload.get('contests', []) if payload else []
        for contest in contests:
            race_defaults = map_contest_to_race_defaults(election, contest)
            canonical_key = race_defaults.pop('canonical_key')
            race, created = Race.objects.update_or_create(
                canonical_key=canonical_key,
                defaults={'election': election, **race_defaults},
            )
            created_count += int(created)
            updated_count += int(not created)
            race.last_synced_at = timezone.now()
            race.save(update_fields=['last_synced_at'])

            if race.race_type == Race.RaceType.CANDIDATE:
                for candidate_payload in contest.get('candidates', []):
                    candidate_name = (candidate_payload.get('name') or '').strip()
                    if not candidate_name:
                        continue
                    _, candidate_created = Candidate.objects.update_or_create(
                        race=race,
                        name=candidate_name,
                        defaults=map_candidate_defaults(candidate_payload),
                    )
                    created_count += int(candidate_created)
                    updated_count += int(not candidate_created)
            else:
                for option_label in measure_option_labels():
                    _, option_created = MeasureOption.objects.get_or_create(race=race, option_label=option_label)
                    created_count += int(option_created)
                    updated_count += int(not option_created)

        election.last_synced_at = timezone.now()
        election.save(update_fields=['last_synced_at'])
        sync_log.records_created = created_count
        sync_log.records_updated = updated_count
        sync_log.status = SyncLog.Status.COMPLETED if sync_log.error_count == 0 else SyncLog.Status.COMPLETED_WITH_WARNINGS
        sync_log.completed_at = timezone.now()
        sync_log.save(update_fields=['records_created', 'records_updated', 'status', 'completed_at'])
        return {'created': created_count, 'updated': updated_count, 'address_label': address_label}
    except CivicAPIForbidden as exc:
        sync_log.error_count = 1
        sync_log.last_error = str(exc)
        sync_log.status = SyncLog.Status.FAILED
        sync_log.completed_at = timezone.now()
        sync_log.save(update_fields=['error_count', 'last_error', 'status', 'completed_at'])
        raise
    except CivicAPIRetryableError as exc:
        sync_log.error_count = 1
        sync_log.last_error = str(exc)
        sync_log.status = SyncLog.Status.COMPLETED_WITH_WARNINGS
        sync_log.completed_at = timezone.now()
        sync_log.save(update_fields=['error_count', 'last_error', 'status', 'completed_at'])
        raise self.retry(exc=exc, countdown=_backoff(self.request.retries))
    except Exception as exc:
        logger.exception('Unexpected Civic sync failure for election=%s address_label=%s', election.source_id, address_label)
        sync_log.error_count = 1
        sync_log.last_error = str(exc)
        sync_log.status = SyncLog.Status.FAILED
        sync_log.completed_at = timezone.now()
        sync_log.save(update_fields=['error_count', 'last_error', 'status', 'completed_at'])
        raise
