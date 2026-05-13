from __future__ import annotations

from datetime import date
from unittest.mock import Mock, patch

import pytest
from celery.exceptions import Retry
from django.test import override_settings

from elections.models import Candidate, Election, Race
from ops.models import SyncLog

from .client import OpenStatesClient, OpenStatesRateLimitError
from .mappers import map_person
from .tasks import US_STATES, sync_openstates_all_states, sync_openstates_legislators


@override_settings(OPENSTATES_API_KEY='test-openstates-key')
@patch('integrations.openstates.client.requests.Session.get')
def test_list_people_sends_expected_params(mock_get):
    response = Mock(status_code=200)
    response.json.return_value = {'results': [], 'pagination': {'page': 1, 'max_page': 1}}
    response.raise_for_status = Mock()
    mock_get.return_value = response

    payload = OpenStatesClient().list_people('CA')

    assert payload == {'results': [], 'pagination': {'page': 1, 'max_page': 1}}
    _, kwargs = mock_get.call_args
    assert kwargs['params']['jurisdiction'] == 'ocd-division/country:us/state:ca'
    assert kwargs['params']['apikey'] == 'test-openstates-key'
    assert kwargs['params']['api_key'] == 'test-openstates-key'
    assert kwargs['timeout'] == 10


@override_settings(OPENSTATES_API_KEY='test-openstates-key')
@patch('integrations.openstates.client.requests.Session.get')
def test_list_people_raises_rate_limit_error_on_429(mock_get):
    response = Mock(status_code=429)
    mock_get.return_value = response

    with pytest.raises(OpenStatesRateLimitError):
        OpenStatesClient().list_people('CA')

    assert mock_get.call_count == 1


@patch.object(OpenStatesClient, 'list_people')
def test_list_people_all_pages_returns_flat_results(mock_list_people):
    mock_list_people.side_effect = [
        {'results': [{'id': 'one'}], 'pagination': {'page': 1, 'max_page': 2}},
        {'results': [{'id': 'two'}], 'pagination': {'page': 2, 'max_page': 2}},
    ]

    results = OpenStatesClient().list_people_all_pages('CA')

    assert results == [{'id': 'one'}, {'id': 'two'}]
    assert mock_list_people.call_count == 2


def test_map_person_extracts_active_legislator_fields():
    mapped = map_person(
        {
            'id': 'os-1',
            'name': 'Alex Smith',
            'party': [
                {'name': 'Retired Party', 'end_date': '2020-01-01'},
                {'name': 'Democratic', 'end_date': ''},
            ],
            'current_role': {
                'title': 'Senator',
                'org_classification': 'upper',
                'district': '5',
                'jurisdiction': 'ocd-division/country:us/state:ca/sldu:5',
            },
            'image': 'https://example.com/alex.jpg',
            'links': [{'url': 'https://alex.example.com'}],
            'email': 'alex@example.com',
            'offices': [
                {'voice': '555-0100', 'address': '123 Capitol Ave', 'classification': 'capitol'},
            ],
        }
    )

    assert mapped['openstates_person_id'] == 'os-1'
    assert mapped['party'] == 'Democratic'
    assert mapped['image_url'] == 'https://example.com/alex.jpg'
    assert mapped['website_url'] == 'https://alex.example.com'
    assert mapped['contact_phone'] == '555-0100'
    assert mapped['contact_office'] == '123 Capitol Ave'
    assert mapped['state'] == 'CA'
    assert mapped['chamber'] == 'upper'
    assert mapped['district'] == '5'
    assert mapped['display_name'] == 'Alex Smith'
    assert mapped['source_metadata']['openstates']['person_id'] == 'os-1'
    assert mapped['source_metadata']['openstates']['jurisdiction'] == 'ocd-division/country:us/state:ca/sldu:5'
    assert mapped['source_metadata']['openstates']['email'] == 'alex@example.com'
    assert mapped['source_metadata']['openstates']['last_synced']


def test_map_person_returns_none_without_current_role():
    assert map_person({'id': 'os-1', 'name': 'Alex Smith', 'current_role': None}) is None


def test_map_person_extracts_state_from_jurisdiction():
    mapped = map_person(
        {
            'id': 'os-1',
            'name': 'Alex Smith',
            'current_role': {
                'org_classification': 'lower',
                'district': '12',
                'jurisdiction': 'ocd-division/country:us/state:ny/sldl:12',
            },
        }
    )

    assert mapped['state'] == 'NY'


@pytest.mark.django_db
def test_sync_openstates_legislators_skips_unchanged_records():
    raw_person = {
        'id': 'os-1',
        'name': 'Alex Smith',
        'current_role': {
            'org_classification': 'upper',
            'district': '5',
            'jurisdiction': 'ocd-division/country:us/state:ca/sldu:5',
        },
    }

    with (
        patch('integrations.openstates.tasks.OpenStatesClient') as mock_client_cls,
        patch('integrations.openstates.tasks.SourceRecordStore') as mock_store_cls,
        patch('integrations.openstates.tasks.CandidateMatcher') as mock_matcher_cls,
    ):
        mock_client_cls.return_value.list_people_all_pages.return_value = [raw_person]
        mock_store_cls.return_value.upsert.return_value = (Mock(), False)

        result = sync_openstates_legislators('CA')

    sync_log = SyncLog.objects.get(task_name='sync_openstates_legislators', address_label='CA')
    assert result['updated'] == 0
    assert sync_log.records_updated == 0
    assert sync_log.records_skipped == 1
    mock_matcher_cls.return_value.enrich.assert_not_called()


@pytest.mark.django_db
@patch('integrations.openstates.tasks.OpenStatesClient')
def test_sync_openstates_legislators_updates_matching_candidate(mock_client_cls):
    election = Election.objects.create(
        name='California General Election',
        election_date=date(2026, 11, 3),
        jurisdiction_level=Election.JurisdictionLevel.STATE,
        state='CA',
        source_id='ca-2026-general',
        status=Election.Status.UPCOMING,
    )
    race = Race.objects.create(
        election=election,
        race_type=Race.RaceType.CANDIDATE,
        office_title='State Senate District 5',
        jurisdiction='California',
        geography_scope='district',
        source=Race.Source.CIVIC_API,
        vote_method=Race.VoteMethod.SINGLE_CHOICE,
        canonical_key='ca-senate-5',
        normalized_office_title='state senate district 5',
    )
    candidate = Candidate.objects.create(race=race, name='Alex Smith')
    mock_client_cls.return_value.list_people_all_pages.return_value = [
        {
            'id': 'os-1',
            'name': 'Alex Smith',
            'party': [{'name': 'Democratic', 'end_date': ''}],
            'current_role': {
                'title': 'Senator',
                'org_classification': 'upper',
                'district': '5',
                'jurisdiction': 'ocd-division/country:us/state:ca/sldu:5',
            },
            'image': 'https://example.com/alex.jpg',
            'links': [{'url': 'https://alex.example.com'}],
            'email': 'alex@example.com',
            'offices': [{'voice': '555-0100', 'address': '123 Capitol Ave'}],
        }
    ]

    result = sync_openstates_legislators('CA')

    candidate.refresh_from_db()
    sync_log = SyncLog.objects.get(task_name='sync_openstates_legislators', address_label='CA')
    assert result['updated'] == 1
    assert candidate.openstates_person_id == 'os-1'
    assert candidate.party == 'Democratic'
    assert candidate.website_url == 'https://alex.example.com'
    assert candidate.source_metadata['openstates']['person_id'] == 'os-1'
    assert sync_log.records_updated == 1
    assert sync_log.records_skipped == 0


@pytest.mark.django_db
def test_sync_openstates_legislators_retries_on_rate_limit():
    with (
        patch('integrations.openstates.tasks.OpenStatesClient') as mock_client_cls,
        patch.object(sync_openstates_legislators, 'retry', side_effect=Retry()) as mock_retry,
    ):
        mock_client_cls.return_value.list_people_all_pages.side_effect = OpenStatesRateLimitError('Too many requests')

        with pytest.raises(Retry):
            sync_openstates_legislators('CA')

    sync_log = SyncLog.objects.get(task_name='sync_openstates_legislators', address_label='CA')
    assert sync_log.status == SyncLog.Status.COMPLETED_WITH_WARNINGS
    assert sync_log.error_count == 1
    assert mock_retry.call_args.kwargs['countdown'] == 600


@patch('integrations.openstates.tasks.sync_openstates_legislators.apply_async')
def test_sync_openstates_all_states_queues_all_states_with_countdown(mock_apply_async):
    sync_openstates_all_states()

    assert mock_apply_async.call_count == len(US_STATES) == 50
    countdowns = [call.kwargs['countdown'] for call in mock_apply_async.call_args_list]
    assert countdowns[0] == 0
    assert countdowns[-1] == (len(US_STATES) - 1) * 60
    assert countdowns == [index * 60 for index in range(len(US_STATES))]
