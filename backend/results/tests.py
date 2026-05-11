from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from elections.models import Candidate, Election, Race
from results.adapters.ca import CaliforniaAdapter
from results.adapters.co import ColoradoAdapter
from results.adapters.ma import MassachusettsAdapter
from results.adapters.base import AdapterResult, ResultRow
from results.adapters.registry import get_adapter
from results.models import OfficialResult
from results.tasks import _process_race_results, ingest_official_results


@pytest.fixture
def election():
    return Election.objects.create(
        name='Official Results Election',
        election_date=date(2026, 11, 3),
        jurisdiction_level=Election.JurisdictionLevel.STATE,
        state='MA',
        source_id=f'results-election-{Election.objects.count() + 1}',
        status=Election.Status.ACTIVE,
    )


@pytest.fixture
def candidate_race(election):
    return Race.objects.create(
        election=election,
        race_type=Race.RaceType.CANDIDATE,
        office_title='Mayor',
        jurisdiction='Boston',
        geography_scope='city',
        certification_status=Race.CertificationStatus.UPCOMING,
        source=Race.Source.CIVIC_API,
        race_status=Race.RaceStatus.ACTIVE,
        vote_method=Race.VoteMethod.SINGLE_CHOICE,
    )


@pytest.mark.django_db
def test_adapter_registry_returns_expected_classes():
    assert get_adapter('MA') is MassachusettsAdapter
    assert get_adapter('CO') is ColoradoAdapter
    assert get_adapter('CA') is CaliforniaAdapter


@pytest.mark.django_db
def test_adapter_registry_returns_none_for_unknown_state():
    assert get_adapter('ZZ') is None


@pytest.mark.django_db
def test_ingest_official_results_marks_partial_results_for_empty_adapter_rows(candidate_race, election):
    ingest_official_results.apply(args=['MA', election.id]).get()

    candidate_race.refresh_from_db()
    assert candidate_race.certification_status == Race.CertificationStatus.PARTIAL_RESULTS


@pytest.mark.django_db
def test_official_result_upsert_is_idempotent(candidate_race):
    Candidate.objects.create(race=candidate_race, name='Jane Smith')
    adapter_result = AdapterResult(
        rows=[
            ResultRow(
                candidate_name='Jane Smith',
                option_label=None,
                vote_count=5000,
                vote_pct=52.3,
                is_winner=True,
                result_type=OfficialResult.ResultType.OFFICIAL,
                raw={'candidate': 'Jane Smith'},
            )
        ],
        source_url='https://example.com/results',
        mapping_confidence='full',
    )

    _process_race_results(candidate_race, adapter_result, 'MA')
    _process_race_results(candidate_race, adapter_result, 'MA')

    assert OfficialResult.objects.count() == 1
    official_result = OfficialResult.objects.get()
    assert official_result.vote_count == 5000
    assert official_result.vote_pct == Decimal('52.30')
    candidate_race.refresh_from_db()
    assert candidate_race.certification_status == Race.CertificationStatus.RESULTS_CERTIFIED
    assert candidate_race.race_status == Race.RaceStatus.ARCHIVED


@pytest.mark.django_db
def test_result_target_valid_allows_write_in_aggregate_rows(candidate_race):
    official_result = OfficialResult.objects.create(
        race=candidate_race,
        candidate=None,
        measure_option=None,
        vote_count=125,
        result_type=OfficialResult.ResultType.OFFICIAL,
        is_write_in_aggregate=True,
        jurisdiction_fragment='Ward 1',
    )

    assert official_result.pk is not None


@pytest.mark.django_db
def test_result_target_valid_rejects_null_targets_without_write_in(candidate_race):
    with pytest.raises(IntegrityError), transaction.atomic():
        OfficialResult.objects.create(
            race=candidate_race,
            candidate=None,
            measure_option=None,
            vote_count=125,
            result_type=OfficialResult.ResultType.OFFICIAL,
            is_write_in_aggregate=False,
        )


@pytest.mark.django_db
def test_official_results_endpoint_returns_public_race_results(candidate_race):
    candidate = Candidate.objects.create(race=candidate_race, name='Jane Smith')
    OfficialResult.objects.create(
        race=candidate_race,
        candidate=candidate,
        vote_count=5000,
        vote_pct=52.3,
        is_winner=True,
        result_type=OfficialResult.ResultType.OFFICIAL,
        source_url='https://example.com/results',
    )

    response = APIClient().get(f'/api/races/{candidate_race.id}/official-results/')

    assert response.status_code == 200
    payload = response.json()
    assert payload['race_id'] == candidate_race.id
    assert payload['certification_status'] == candidate_race.certification_status
    assert payload['source_url'] == 'https://example.com/results'
    assert payload['results'][0]['candidate_name'] == 'Jane Smith'
    assert payload['results'][0]['option_label'] is None
