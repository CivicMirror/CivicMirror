from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from django.core.cache import cache
from integrations.congress.client import (
    DATA_CACHE_KEY_PREFIX,
    ETAG_CACHE_KEY_PREFIX,
    LEGISLATORS_CURRENT_URL,
    CongressLegislatorsClient,
)
from integrations.congress.mappers import map_legislator
from integrations.congress.tasks import sync_congress_legislators
from ops.models import SyncLog, SourceRecord


@pytest.mark.django_db
@patch('integrations.congress.client.requests.get')
def test_fetch_if_changed_caches_etag_and_handles_not_modified(mock_get):
    cache.clear()
    data = [{'id': {'bioguide': 'A000360'}}]
    first_response = Mock(status_code=200, headers={'ETag': 'etag-v1'})
    first_response.json.return_value = data
    second_response = Mock(status_code=304, headers={})
    third_response = Mock(status_code=200, headers={'ETag': 'etag-v2'})
    third_response.json.return_value = data + [{'id': {'bioguide': 'B001234'}}]
    mock_get.side_effect = [first_response, second_response, third_response]

    client = CongressLegislatorsClient()

    first_payload, first_changed = client.fetch_if_changed(LEGISLATORS_CURRENT_URL)
    assert first_changed is True
    assert first_payload == data
    assert cache.get(f'{ETAG_CACHE_KEY_PREFIX}{LEGISLATORS_CURRENT_URL}') == 'etag-v1'

    second_payload, second_changed = client.fetch_if_changed(LEGISLATORS_CURRENT_URL)
    assert second_changed is False
    assert second_payload is None
    assert mock_get.call_args_list[1].kwargs['headers']['If-None-Match'] == 'etag-v1'

    third_payload, third_changed = client.fetch_if_changed(LEGISLATORS_CURRENT_URL)
    assert third_changed is True
    assert third_payload == data + [{'id': {'bioguide': 'B001234'}}]
    assert cache.get(f'{ETAG_CACHE_KEY_PREFIX}{LEGISLATORS_CURRENT_URL}') == 'etag-v2'
    assert cache.get(f'{DATA_CACHE_KEY_PREFIX}{LEGISLATORS_CURRENT_URL}') == third_payload


@pytest.mark.django_db
def test_map_legislator_maps_current_representative():
    raw = {
        'id': {'bioguide': 'A000360', 'fec': ['H2CA12001']},
        'name': {'official_full': 'Ada Lovelace', 'first': 'Ada', 'last': 'Lovelace'},
        'terms': [
            {
                'type': 'rep',
                'state': 'CA',
                'district': 5,
                'start': '2023-01-03',
                'end': '2099-01-03',
                'party': 'Independent',
                'phone': '202-555-0100',
                'address': '123 Longworth House Office Building',
                'url': 'https://example.com/ada',
            }
        ],
        'social': {'twitter': 'adal', 'facebook': 'ada.fb', 'youtube': 'ada.yt'},
    }

    mapped = map_legislator(raw)

    assert mapped is not None
    assert mapped['bioguide_id'] == 'A000360'
    assert mapped['fec_candidate_id'] == 'H2CA12001'
    assert mapped['office_type'] == 'H'
    assert mapped['district'] == '05'
    assert mapped['state'] == 'CA'
    assert mapped['contact_phone'] == '202-555-0100'
    assert mapped['contact_office'] == '123 Longworth House Office Building'
    assert mapped['website_url'] == 'https://example.com/ada'
    assert mapped['official_full_name'] == 'Ada Lovelace'
    assert mapped['source_metadata']['congress']['official_full'] == 'Ada Lovelace'
    assert mapped['source_metadata']['congress']['twitter'] == 'adal'


@pytest.mark.django_db
def test_map_legislator_maps_current_senator():
    raw = {
        'id': {'bioguide': 'B000001'},
        'name': {'official_full': 'Bob Stone', 'first': 'Bob', 'last': 'Stone'},
        'terms': [
            {
                'type': 'sen',
                'state': 'NY',
                'start': '2021-01-03',
                'end': '2099-01-03',
                'party': 'Democratic',
            }
        ],
    }

    mapped = map_legislator(raw)

    assert mapped is not None
    assert mapped['office_type'] == 'S'
    assert mapped['district'] == ''
    assert mapped['state'] == 'NY'


@pytest.mark.django_db
def test_map_legislator_skips_inactive_legislator():
    raw = {
        'id': {'bioguide': 'C000001'},
        'name': {'official_full': 'Chris Past', 'first': 'Chris', 'last': 'Past'},
        'terms': [
            {
                'type': 'rep',
                'state': 'TX',
                'district': 3,
                'start': '2019-01-03',
                'end': '2020-01-03',
                'party': 'Independent',
            }
        ],
    }

    assert map_legislator(raw) is None


@pytest.mark.django_db
def test_sync_congress_legislators_logs_no_change_detected():
    with patch('integrations.congress.tasks.CongressLegislatorsClient.fetch_current', return_value=(None, False)):
        result = sync_congress_legislators.apply().get()

    sync_log = SyncLog.objects.get(task_name='sync_congress_legislators')
    assert result == {'updated': 0, 'skipped': 0, 'warnings': 0}
    assert sync_log.status == SyncLog.Status.COMPLETED
    assert sync_log.records_updated == 0
    assert sync_log.last_error == 'no changes detected'


@pytest.mark.django_db
def test_sync_congress_legislators_enriches_active_legislator():
    raw = {
        'id': {'bioguide': 'A000360', 'fec': ['H2CA12001']},
        'name': {'official_full': 'Ada Lovelace', 'first': 'Ada', 'last': 'Lovelace'},
        'terms': [
            {
                'type': 'rep',
                'state': 'CA',
                'district': 5,
                'start': '2023-01-03',
                'end': '2099-01-03',
                'party': 'Independent',
            }
        ],
    }

    with patch('integrations.congress.tasks.CongressLegislatorsClient.fetch_current', return_value=([raw], True)), patch(
        'integrations.congress.tasks.CandidateMatcher.enrich', return_value=(Mock(), 'enriched')
    ) as mock_enrich:
        result = sync_congress_legislators.apply().get()

    sync_log = SyncLog.objects.get(task_name='sync_congress_legislators')
    assert result['updated'] == 1
    assert sync_log.status == SyncLog.Status.COMPLETED
    assert SourceRecord.objects.filter(source='congress', external_id='A000360').exists()
    mock_enrich.assert_called_once()
    assert mock_enrich.call_args.kwargs['race'] is None
    assert mock_enrich.call_args.kwargs['external_id'] == 'A000360'
    assert mock_enrich.call_args.kwargs['enrichment_payload']['bioguide_id'] == 'A000360'


@pytest.mark.django_db
def test_sync_congress_legislators_logs_ambiguous_match_as_warning():
    raw = {
        'id': {'bioguide': 'A000360'},
        'name': {'official_full': 'Ada Lovelace', 'first': 'Ada', 'last': 'Lovelace'},
        'terms': [
            {
                'type': 'sen',
                'state': 'CA',
                'start': '2023-01-03',
                'end': '2099-01-03',
                'party': 'Independent',
            }
        ],
    }

    with patch('integrations.congress.tasks.CongressLegislatorsClient.fetch_current', return_value=([raw], True)), patch(
        'integrations.congress.tasks.CandidateMatcher.enrich', return_value=(None, 'ambiguous')
    ):
        result = sync_congress_legislators.apply().get()

    sync_log = SyncLog.objects.get(task_name='sync_congress_legislators')
    assert result['warnings'] == 1
    assert sync_log.status == SyncLog.Status.COMPLETED_WITH_WARNINGS
    assert 'ambiguous:A000360' in sync_log.last_error
