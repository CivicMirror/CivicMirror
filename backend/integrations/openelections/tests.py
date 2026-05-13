from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest

from elections.models import Candidate, Election, Race
from ops.models import SyncLog
from results.models import OfficialResult

from .mappers import map_result_row, parse_result_file_metadata
from .tasks import check_openelections_new_results, ingest_openelections_state


@pytest.fixture
def openelections_row():
    return {
        'county': 'Suffolk',
        'precinct': 'Ward 1',
        'office': 'President',
        'district': '',
        'party': 'Democratic',
        'candidate': 'Jane Smith',
        'votes': '1234',
        'winner': 'True',
    }


def test_map_result_row_returns_normalized_dict(openelections_row):
    mapped = map_result_row(openelections_row, 'ma', '2020-11-03', 'president')

    assert mapped == {
        'candidate_name': 'Jane Smith',
        'party': 'Democratic',
        'office': 'President',
        'district': None,
        'state': 'MA',
        'election_date': '2020-11-03',
        'votes': 1234,
        'winner': True,
        'raw_county': 'Suffolk',
        'raw_precinct': 'Ward 1',
    }


def test_map_result_row_returns_none_without_candidate(openelections_row):
    row = dict(openelections_row, candidate='')

    assert map_result_row(row, 'MA', '2020-11-03', 'president') is None


def test_map_result_row_keeps_zero_votes(openelections_row):
    row = dict(openelections_row, votes='0')

    mapped = map_result_row(row, 'MA', '2020-11-03', 'president')

    assert mapped is not None
    assert mapped['votes'] == 0


def test_parse_result_file_metadata_extracts_date_and_office():
    assert parse_result_file_metadata('20201103__ma__general__president.csv') == ('2020-11-03', 'president')


@pytest.mark.django_db
@patch('integrations.openelections.tasks.ingest_openelections_state.delay')
@patch('integrations.openelections.tasks.OpenElectionsClient')
def test_check_openelections_new_results_queues_new_files(mock_client_cls, mock_delay):
    client = mock_client_cls.return_value
    client.get_latest_commit_sha.return_value = 'sha-new'
    client.list_result_files.return_value = [
        {'path': '20201103__ma__general__president.csv', 'sha': 'file-sha', 'download_url': 'https://example.com/p.csv'}
    ]
    SyncLog.objects.create(
        source='openelections',
        task_name='check_openelections_new_results',
        address_label='MA',
        status=SyncLog.Status.COMPLETED,
        notes='last_processed_commit_sha=sha-old',
    )

    result = check_openelections_new_results('MA')

    assert result['queued'] == 1
    client.list_result_files.assert_called_once_with('MA', since_sha='sha-old')
    mock_delay.assert_called_once_with(state='MA', file_path='20201103__ma__general__president.csv', election_date='2020-11-03')
    sync_log = SyncLog.objects.latest('id')
    assert sync_log.records_created == 1
    assert sync_log.notes == 'last_processed_commit_sha=sha-new'


@pytest.mark.django_db
@patch('integrations.openelections.tasks.ingest_openelections_state.delay')
@patch('integrations.openelections.tasks.OpenElectionsClient')
def test_check_openelections_new_results_skips_same_sha(mock_client_cls, mock_delay):
    client = mock_client_cls.return_value
    client.get_latest_commit_sha.return_value = 'sha-same'
    SyncLog.objects.create(
        source='openelections',
        task_name='check_openelections_new_results',
        address_label='MA',
        status=SyncLog.Status.COMPLETED,
        notes='last_processed_commit_sha=sha-same',
    )

    result = check_openelections_new_results('MA')

    assert result['queued'] == 0
    client.list_result_files.assert_not_called()
    mock_delay.assert_not_called()
    sync_log = SyncLog.objects.latest('id')
    assert sync_log.last_error == 'no changes detected'


@pytest.mark.django_db
@patch('integrations.openelections.tasks.OpenElectionsClient')
def test_ingest_openelections_state_processes_rows(mock_client_cls):
    election = Election.objects.create(
        name='Massachusetts General Election',
        election_date=date(2020, 11, 3),
        jurisdiction_level=Election.JurisdictionLevel.STATE,
        state='MA',
        source_id='ma-2020-general',
        status=Election.Status.ARCHIVED,
    )
    race = Race.objects.create(
        election=election,
        race_type=Race.RaceType.CANDIDATE,
        office_title='President',
        jurisdiction='Massachusetts',
        geography_scope='statewide',
        source=Race.Source.CIVIC_API,
        vote_method=Race.VoteMethod.SINGLE_CHOICE,
        canonical_key='ma-president-2020',
        normalized_office_title='president',
        ocd_division_id='ocd-division/country:us/state:ma',
    )
    candidate = Candidate.objects.create(race=race, name='Jane Smith')
    client = mock_client_cls.return_value
    client.list_result_files.return_value = [
        {'path': '20201103__ma__general__president.csv', 'sha': 'file-sha', 'download_url': 'https://example.com/p.csv'}
    ]
    client.download_csv.return_value = [
        {
            'county': 'Suffolk',
            'precinct': 'Ward 1',
            'office': 'President',
            'district': '',
            'party': 'Democratic',
            'candidate': 'Jane Smith',
            'votes': '1234',
            'winner': 'True',
        }
    ]

    result = ingest_openelections_state('MA', '20201103__ma__general__president.csv', '2020-11-03')

    assert result['created'] == 1
    candidate.refresh_from_db()
    official_result = OfficialResult.objects.get(race=race, candidate=candidate)
    assert official_result.vote_count == 1234
    assert official_result.is_winner is True
    assert candidate.source_metadata['openelections']['file_path'] == '20201103__ma__general__president.csv'
    sync_log = SyncLog.objects.latest('id')
    assert sync_log.records_created == 1
    assert sync_log.error_count == 0


@pytest.mark.django_db
@patch('integrations.openelections.tasks.OpenElectionsClient')
def test_ingest_openelections_state_counts_no_race_found_warning(mock_client_cls):
    client = mock_client_cls.return_value
    client.list_result_files.return_value = [
        {'path': '20201103__ma__general__president.csv', 'sha': 'file-sha', 'download_url': 'https://example.com/p.csv'}
    ]
    client.download_csv.return_value = [
        {
            'county': 'Suffolk',
            'precinct': 'Ward 1',
            'office': 'President',
            'district': '',
            'party': 'Democratic',
            'candidate': 'Jane Smith',
            'votes': '1234',
            'winner': 'True',
        }
    ]

    result = ingest_openelections_state('MA', '20201103__ma__general__president.csv', '2020-11-03')

    assert result['warnings'] == 1
    sync_log = SyncLog.objects.latest('id')
    assert sync_log.status == SyncLog.Status.COMPLETED_WITH_WARNINGS
    assert sync_log.error_count == 1
