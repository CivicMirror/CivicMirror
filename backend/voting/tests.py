from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from elections.models import Candidate, Election, Race
from voting.models import MockVote

User = get_user_model()


@pytest.fixture
def election():
    return Election.objects.create(
        name='2026 General Election',
        election_date=(timezone.now() + timezone.timedelta(days=30)).date(),
        jurisdiction_level=Election.JurisdictionLevel.STATE,
        state='MA',
        source_id=f'election-{Election.objects.count() + 1}',
        status=Election.Status.ACTIVE,
    )


@pytest.fixture
def active_candidate_race(election):
    return Race.objects.create(
        election=election,
        race_type=Race.RaceType.CANDIDATE,
        office_title='U.S. Senate',
        jurisdiction='MA',
        geography_scope='statewide',
        voting_opens=timezone.now() - timezone.timedelta(days=1),
        voting_closes=timezone.now() + timezone.timedelta(days=1),
        certification_status=Race.CertificationStatus.UPCOMING,
        source=Race.Source.CIVIC_API,
        race_status=Race.RaceStatus.ACTIVE,
        vote_method=Race.VoteMethod.SINGLE_CHOICE,
    )


@pytest.fixture
def auth_client() -> tuple[APIClient, object]:
    username = f'voter-{User.objects.count() + 1}'
    password = 'Password123!'
    user = User.objects.create_user(username=username, password=password)
    client = APIClient()
    login_response = client.post('/api/auth/login/', {'username': username, 'password': password}, format='json')
    assert login_response.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Token {login_response.json()['token']}")
    return client, user


@pytest.mark.django_db
def test_authenticated_user_can_cast_vote(auth_client, active_candidate_race):
    client, _ = auth_client
    candidate = Candidate.objects.create(race=active_candidate_race, name='Jane Smith')

    response = client.post(f'/api/races/{active_candidate_race.id}/vote/', {'candidate_id': candidate.id}, format='json')

    assert response.status_code == 201
    assert response.json()['candidate_id'] == candidate.id
    assert MockVote.objects.filter(race=active_candidate_race).count() == 1


@pytest.mark.django_db
def test_unauthenticated_vote_returns_401(active_candidate_race):
    candidate = Candidate.objects.create(race=active_candidate_race, name='Jane Smith')

    response = APIClient().post(f'/api/races/{active_candidate_race.id}/vote/', {'candidate_id': candidate.id}, format='json')

    assert response.status_code == 401
    assert response.json()['code'] == 'not_authenticated'


@pytest.mark.django_db
def test_duplicate_vote_returns_409(auth_client, active_candidate_race):
    client, user = auth_client
    candidate = Candidate.objects.create(race=active_candidate_race, name='Jane Smith')
    MockVote.objects.create(user=user, race=active_candidate_race, candidate=candidate)

    response = client.post(f'/api/races/{active_candidate_race.id}/vote/', {'candidate_id': candidate.id}, format='json')

    assert response.status_code == 409
    assert response.json()['code'] == 'already_voted'


@pytest.mark.django_db
def test_wrong_race_option_returns_400(auth_client, active_candidate_race, election):
    client, _ = auth_client
    other_race = Race.objects.create(
        election=election,
        race_type=Race.RaceType.CANDIDATE,
        office_title='Attorney General',
        jurisdiction='MA',
        geography_scope='statewide',
        voting_opens=timezone.now() - timezone.timedelta(days=1),
        voting_closes=timezone.now() + timezone.timedelta(days=1),
        certification_status=Race.CertificationStatus.UPCOMING,
        source=Race.Source.CIVIC_API,
        race_status=Race.RaceStatus.ACTIVE,
        vote_method=Race.VoteMethod.SINGLE_CHOICE,
    )
    wrong_candidate = Candidate.objects.create(race=other_race, name='Wrong Race Candidate')

    response = client.post(f'/api/races/{active_candidate_race.id}/vote/', {'candidate_id': wrong_candidate.id}, format='json')

    assert response.status_code == 400
    assert response.json()['code'] == 'invalid_option'


@pytest.mark.django_db
def test_tally_counts_correct(auth_client, active_candidate_race):
    client, user = auth_client
    candidate_one = Candidate.objects.create(race=active_candidate_race, name='Jane Smith')
    candidate_two = Candidate.objects.create(race=active_candidate_race, name='John Doe')
    other_user = User.objects.create_user(username='other-voter', password='Password123!')

    MockVote.objects.create(user=user, race=active_candidate_race, candidate=candidate_one)
    MockVote.objects.create(user=other_user, race=active_candidate_race, candidate=candidate_two)

    response = client.get(f'/api/races/{active_candidate_race.id}/tally/')

    assert response.status_code == 200
    payload = response.json()
    assert payload['total_votes'] == 2
    counts = {option['label']: option['count'] for option in payload['options']}
    assert counts == {'Jane Smith': 1, 'John Doe': 1}
    assert payload['breakdowns'] == {'age_range': {}, 'country': {}, 'us_state': {}}


@pytest.mark.django_db
def test_vote_history_returns_only_own_votes(auth_client, active_candidate_race):
    client, user = auth_client
    candidate = Candidate.objects.create(race=active_candidate_race, name='Jane Smith')
    other_user = User.objects.create_user(username='other-history', password='Password123!')

    MockVote.objects.create(user=user, race=active_candidate_race, candidate=candidate)
    MockVote.objects.create(user=other_user, race=active_candidate_race, candidate=candidate)

    response = client.get('/api/users/me/votes/')

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]['choice'] == {'type': 'candidate', 'id': candidate.id, 'label': 'Jane Smith'}
    assert payload[0]['office_title'] == 'U.S. Senate'


@pytest.mark.django_db
def test_race_detail_includes_tally_summary_and_viewer_choice(auth_client, active_candidate_race):
    client, user = auth_client
    candidate = Candidate.objects.create(race=active_candidate_race, name='Jane Smith')
    MockVote.objects.create(user=user, race=active_candidate_race, candidate=candidate)

    response = client.get(f'/api/races/{active_candidate_race.id}/')

    assert response.status_code == 200
    payload = response.json()
    assert payload['viewer_has_voted'] is True
    assert payload['viewer_choice'] == {'type': 'candidate', 'id': candidate.id, 'label': 'Jane Smith'}
    assert payload['tally_summary']['total_votes'] == 1
    assert payload['tally_summary']['options'][0]['count'] == 1
