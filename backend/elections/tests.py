from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from elections.models import Candidate, Election, Race
from elections.tasks import auto_close_community_races

User = get_user_model()


def auth_client(username: str = 'community-user', password: str = 'Password123!'):
    user = User.objects.create_user(username=username, password=password)
    client = APIClient()
    login_response = client.post('/api/auth/login/', {'username': username, 'password': password}, format='json')
    assert login_response.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Token {login_response.json()['token']}")
    return client, user


@pytest.fixture
def submission_payload():
    return {
        'race_type': 'candidate',
        'office_title': 'City Council District 3',
        'jurisdiction': 'city',
        'election_date': (timezone.localdate() + timezone.timedelta(days=30)).isoformat(),
        'location_name': 'Boston City Hall',
        'source_links': ['https://example.com/race'],
        'candidates': [
            {
                'name': 'Jamie Rivera',
                'party': 'Independent',
                'description': 'Neighborhood organizer',
                'image_url': 'https://example.com/jamie.png',
                'website_url': 'https://example.com/jamie',
                'candidate_type': 'running',
            }
        ],
    }


@pytest.mark.django_db
def test_local_race_submission_creates_pending_community_race(submission_payload):
    client, user = auth_client()

    response = client.post('/api/races/local/', submission_payload, format='json')

    assert response.status_code == 201
    race = Race.objects.get(pk=response.json()['id'])
    assert race.source == Race.Source.COMMUNITY
    assert race.community_status == Race.CommunityStatus.PENDING_REVIEW
    assert race.race_status == Race.RaceStatus.PENDING_REVIEW
    assert race.submitter.user == user
    assert race.submitted_at is not None
    assert race.location_name == 'Boston City Hall'
    candidate = Candidate.objects.get(race=race)
    assert candidate.name == 'Jamie Rivera'
    assert candidate.website_url == 'https://example.com/jamie'


@pytest.mark.django_db
def test_local_race_submission_conflict_detection_returns_warning(submission_payload):
    client, _ = auth_client()
    election_date = timezone.datetime.fromisoformat(submission_payload['election_date']).date()
    election = Election.objects.create(
        name='Existing Local Election',
        election_date=election_date,
        jurisdiction_level=Election.JurisdictionLevel.LOCAL,
        source_id='existing-local-election',
        status=Election.Status.UPCOMING,
    )
    Race.objects.create(
        election=election,
        race_type=Race.RaceType.CANDIDATE,
        office_title='City Council District 3',
        jurisdiction='city',
        geography_scope='city',
        source=Race.Source.CIVIC_API,
        race_status=Race.RaceStatus.ACTIVE,
        vote_method=Race.VoteMethod.SINGLE_CHOICE,
    )

    response = client.post('/api/races/local/', submission_payload, format='json')

    assert response.status_code == 200
    payload = response.json()
    assert payload['conflict'] is True
    assert payload['message'] == 'Similar races found. Confirm to submit anyway.'
    assert len(payload['races']) == 1


@pytest.mark.django_db
def test_force_submit_bypasses_conflict_check(submission_payload):
    client, _ = auth_client()
    election_date = timezone.datetime.fromisoformat(submission_payload['election_date']).date()
    election = Election.objects.create(
        name='Existing Local Election',
        election_date=election_date,
        jurisdiction_level=Election.JurisdictionLevel.LOCAL,
        source_id='existing-local-election-force',
        status=Election.Status.UPCOMING,
    )
    Race.objects.create(
        election=election,
        race_type=Race.RaceType.CANDIDATE,
        office_title='City Council District 3',
        jurisdiction='city',
        geography_scope='city',
        source=Race.Source.CIVIC_API,
        race_status=Race.RaceStatus.ACTIVE,
        vote_method=Race.VoteMethod.SINGLE_CHOICE,
    )

    response = client.post('/api/races/local/', {**submission_payload, 'force_submit': True}, format='json')

    assert response.status_code == 201
    assert Race.objects.filter(office_title='City Council District 3').count() == 2


@pytest.mark.django_db
def test_unauthenticated_local_submission_returns_401(submission_payload):
    response = APIClient().post('/api/races/local/', submission_payload, format='json')

    assert response.status_code == 401
    assert response.json()['code'] == 'not_authenticated'


@pytest.mark.django_db
def test_auto_close_task_archives_eligible_community_races():
    election = Election.objects.create(
        name='Past Community Election',
        election_date=timezone.localdate() - timezone.timedelta(days=20),
        jurisdiction_level=Election.JurisdictionLevel.LOCAL,
        source_id='past-community-election',
        status=Election.Status.ARCHIVED,
    )
    race = Race.objects.create(
        election=election,
        race_type=Race.RaceType.CANDIDATE,
        office_title='School Committee',
        jurisdiction='town',
        geography_scope='town',
        source=Race.Source.COMMUNITY,
        community_status=Race.CommunityStatus.ACTIVE,
        race_status=Race.RaceStatus.ACTIVE,
        vote_method=Race.VoteMethod.SINGLE_CHOICE,
    )

    auto_close_community_races()
    race.refresh_from_db()

    assert race.race_status == Race.RaceStatus.ARCHIVED


@pytest.mark.django_db
def test_public_race_views_hide_pending_community_races():
    client = APIClient()
    election = Election.objects.create(
        name='Public Local Election',
        election_date=timezone.localdate() + timezone.timedelta(days=30),
        jurisdiction_level=Election.JurisdictionLevel.LOCAL,
        source_id='public-local-election',
        status=Election.Status.UPCOMING,
    )
    hidden_race = Race.objects.create(
        election=election,
        race_type=Race.RaceType.CANDIDATE,
        office_title='Hidden Race',
        jurisdiction='city',
        geography_scope='city',
        source=Race.Source.COMMUNITY,
        community_status=Race.CommunityStatus.PENDING_REVIEW,
        race_status=Race.RaceStatus.PENDING_REVIEW,
        vote_method=Race.VoteMethod.SINGLE_CHOICE,
    )
    visible_race = Race.objects.create(
        election=election,
        race_type=Race.RaceType.CANDIDATE,
        office_title='Visible Race',
        jurisdiction='city',
        geography_scope='city',
        source=Race.Source.COMMUNITY,
        community_status=Race.CommunityStatus.ACTIVE,
        race_status=Race.RaceStatus.ACTIVE,
        vote_method=Race.VoteMethod.SINGLE_CHOICE,
    )

    list_response = client.get('/api/races/')
    detail_response = client.get(f'/api/races/{hidden_race.id}/')
    visible_detail = client.get(f'/api/races/{visible_race.id}/')

    assert list_response.status_code == 200
    returned_ids = {result['id'] for result in list_response.json()['results']}
    assert hidden_race.id not in returned_ids
    assert visible_race.id in returned_ids
    assert detail_response.status_code == 404
    assert visible_detail.status_code == 200
