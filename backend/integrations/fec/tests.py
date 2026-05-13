from unittest.mock import Mock, call, patch

import pytest

from integrations.fec.client import FECAPIForbidden, FECClient
from integrations.fec.mappers import map_candidate
from integrations.fec.tasks import sync_fec_candidates
from integrations.orchestrator.exceptions import NoRaceFoundError
from ops.models import SyncLog


@pytest.fixture
def fec_candidate_payload():
    return {
        'candidate_id': 'H4MA07001',
        'name': 'Alex Rivera',
        'office': 'H',
        'office_full': 'U.S. House',
        'state': 'MA',
        'district': '07',
        'party_full': 'Democratic Party',
        'incumbent_challenge_full': 'Incumbent',
        'election_years': [2024],
        'candidate_status': 'C',
    }


@patch('integrations.fec.client.time.sleep', return_value=None)
def test_fec_client_list_candidates_sends_expected_params(mock_sleep, settings):
    settings.FEC_API_KEY = 'test-fec-key'
    client = FECClient()
    response = Mock(status_code=200)
    response.json.return_value = {'results': [], 'pagination': {'pages': 1}}

    with patch.object(client.session, 'get', return_value=response) as mock_get:
        payload = client.list_candidates(office='H', state='MA', cycle=2024, page=2)

    assert payload == {'results': [], 'pagination': {'pages': 1}}
    mock_get.assert_called_once_with(
        'https://api.open.fec.gov/v1/candidates/',
        params={
            'office': 'H',
            'state': 'MA',
            'election_year': 2024,
            'per_page': 100,
            'page': 2,
            'api_key': 'test-fec-key',
        },
        timeout=10,
    )


def test_fec_client_list_candidates_all_pages_concatenates_results(settings):
    settings.FEC_API_KEY = 'test-fec-key'
    client = FECClient()

    with patch.object(
        client,
        'list_candidates',
        side_effect=[
            {'results': [{'candidate_id': 'C1'}], 'pagination': {'pages': 2}},
            {'results': [{'candidate_id': 'C2'}], 'pagination': {'pages': 2}},
        ],
    ) as mock_list_candidates:
        results = client.list_candidates_all_pages(office='S', state='MA', cycle=2024)

    assert results == [{'candidate_id': 'C1'}, {'candidate_id': 'C2'}]
    assert mock_list_candidates.call_args_list == [
        call(office='S', state='MA', cycle=2024, page=1),
        call(office='S', state='MA', cycle=2024, page=2),
    ]


def test_map_candidate_maps_realistic_payload_and_skips_inactive_status(fec_candidate_payload):
    mapped = map_candidate(fec_candidate_payload)

    assert mapped == {
        'fec_candidate_id': 'H4MA07001',
        'office_type': 'H',
        'state': 'MA',
        'district': '07',
        'party': 'Democratic Party',
        'incumbent': True,
        'normalized_office_title': 'u.s. house',
        'source_metadata': {
            'fec': {
                'candidate_id': 'H4MA07001',
                'name': 'Alex Rivera',
                'office': 'H',
                'office_full': 'U.S. House',
                'state': 'MA',
                'district': '07',
                'party_full': 'Democratic Party',
                'incumbent_challenge_full': 'Incumbent',
                'election_years': [2024],
                'candidate_status': 'C',
            }
        },
    }

    skipped_payload = dict(fec_candidate_payload, candidate_status='N')
    assert map_candidate(skipped_payload) is None


@pytest.mark.django_db
def test_sync_fec_candidates_skips_unchanged_records_and_no_race_matches(settings, fec_candidate_payload):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    unchanged_record = Mock(linked_race_id=None, linked_candidate_id=None)
    changed_record = Mock(linked_race_id=None, linked_candidate_id=None)

    with patch('integrations.fec.tasks.US_STATES', ['MA']), patch(
        'integrations.fec.tasks.FECClient'
    ) as mock_client_cls, patch('integrations.fec.tasks.SourceRecordStore') as mock_store_cls, patch(
        'integrations.fec.tasks.RaceMatcher'
    ) as mock_race_matcher_cls, patch('integrations.fec.tasks.CandidateMatcher') as mock_candidate_matcher_cls, patch(
        'integrations.fec.tasks.resolve_ocd_id', return_value=None
    ):
        mock_client = mock_client_cls.return_value
        mock_client.list_candidates_all_pages.side_effect = [
            [fec_candidate_payload, dict(fec_candidate_payload, candidate_id='H4MA07002')],
            [],
            [],
        ]
        mock_store = mock_store_cls.return_value
        mock_store.upsert.side_effect = [
            (unchanged_record, False),
            (changed_record, True),
        ]
        mock_race_matcher = mock_race_matcher_cls.return_value
        mock_race_matcher.find_or_create.side_effect = [NoRaceFoundError('no race')]

        result = sync_fec_candidates.apply(kwargs={'cycle_year': 2024}).get()

    assert result == {'created': 1, 'updated': 0, 'skipped': 2}
    mock_race_matcher.find_or_create.assert_called_once()
    mock_candidate_matcher_cls.return_value.enrich.assert_not_called()
    sync_log = SyncLog.objects.latest('id')
    assert sync_log.records_skipped == 2
    assert sync_log.error_count == 0
    assert sync_log.status == SyncLog.Status.COMPLETED


@pytest.mark.django_db
def test_sync_fec_candidates_marks_sync_log_failed_on_forbidden(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = False

    with patch('integrations.fec.tasks.US_STATES', ['MA']), patch(
        'integrations.fec.tasks.FECClient'
    ) as mock_client_cls:
        mock_client_cls.return_value.list_candidates_all_pages.side_effect = FECAPIForbidden('forbidden')

        result = sync_fec_candidates.apply(kwargs={'cycle_year': 2024})

    assert result.failed()
    sync_log = SyncLog.objects.latest('id')
    assert sync_log.status == SyncLog.Status.FAILED
    assert sync_log.last_error == 'forbidden'
