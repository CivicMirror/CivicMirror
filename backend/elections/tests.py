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


# ── Scope filtering ───────────────────────────────────────────────────────────

def _make_election(source_id, state=None, level=Election.JurisdictionLevel.STATE):
    return Election.objects.create(
        name=f'Election {source_id}',
        election_date=timezone.localdate() + timezone.timedelta(days=30),
        jurisdiction_level=level,
        state=state,
        source_id=source_id,
        status=Election.Status.UPCOMING,
    )


def _make_race(election, office_title='Governor', *, source=Race.Source.CIVIC_API):
    return Race.objects.create(
        election=election,
        race_type=Race.RaceType.CANDIDATE,
        office_title=office_title,
        jurisdiction='statewide',
        geography_scope='statewide',
        source=source,
        race_status=Race.RaceStatus.ACTIVE,
        vote_method=Race.VoteMethod.SINGLE_CHOICE,
    )


@pytest.mark.django_db
def test_scope_national_returns_only_national_races():
    national_election = _make_election('nat-1', level=Election.JurisdictionLevel.NATIONAL)
    nc_election = _make_election('nc-1', state='NC')
    national_race = _make_race(national_election, 'President')
    nc_race = _make_race(nc_election, 'NC Governor')

    response = APIClient().get('/api/races/', {'scope': 'national'})

    assert response.status_code == 200
    ids = {r['id'] for r in response.json()['results']}
    assert national_race.id in ids
    assert nc_race.id not in ids


@pytest.mark.django_db
def test_scope_state_returns_only_statewide_races_for_selected_state():
    national_election = _make_election('nat-2', level=Election.JurisdictionLevel.NATIONAL)
    nc_election = _make_election('nc-2', state='NC')
    ga_election = _make_election('ga-2', state='GA')
    national_race = _make_race(national_election, 'President')
    nc_race = _make_race(nc_election, 'NC Governor')
    ga_race = _make_race(ga_election, 'GA Governor')
    local_nc_race = Race.objects.create(
        election=nc_election,
        race_type=Race.RaceType.CANDIDATE,
        office_title='Charlotte City Council',
        jurisdiction='Charlotte',
        geography_scope='city',
        source=Race.Source.CIVIC_API,
        race_status=Race.RaceStatus.ACTIVE,
        vote_method=Race.VoteMethod.SINGLE_CHOICE,
    )

    response = APIClient().get('/api/races/', {'scope': 'state', 'state': 'NC'})

    assert response.status_code == 200
    ids = {r['id'] for r in response.json()['results']}
    assert nc_race.id in ids
    assert national_race.id not in ids
    assert ga_race.id not in ids
    assert local_nc_race.id not in ids


@pytest.mark.django_db
def test_scope_state_includes_district_scope_races():
    """Civic API often returns geography_scope='district' for state-level contests
    (congressional races, constitutional amendments). These must appear in state scope."""
    nc_election = _make_election('nc-district', state='NC')
    statewide_race = _make_race(nc_election, 'NC Governor')  # geography_scope='statewide'
    district_race = Race.objects.create(
        election=nc_election,
        race_type=Race.RaceType.CANDIDATE,
        office_title='U.S. Representative',
        jurisdiction='North Carolina',
        geography_scope='district',
        source=Race.Source.CIVIC_API,
        race_status=Race.RaceStatus.ACTIVE,
        vote_method=Race.VoteMethod.SINGLE_CHOICE,
    )
    city_race = Race.objects.create(
        election=nc_election,
        race_type=Race.RaceType.CANDIDATE,
        office_title='Raleigh Mayor',
        jurisdiction='Raleigh',
        geography_scope='city',
        source=Race.Source.CIVIC_API,
        race_status=Race.RaceStatus.ACTIVE,
        vote_method=Race.VoteMethod.SINGLE_CHOICE,
    )

    response = APIClient().get('/api/races/', {'scope': 'state', 'state': 'NC'})

    assert response.status_code == 200
    ids = {r['id'] for r in response.json()['results']}
    assert statewide_race.id in ids
    assert district_race.id in ids
    assert city_race.id not in ids


@pytest.mark.django_db
def test_scope_state_without_state_param_returns_empty():
    _make_race(_make_election('nc-3', state='NC'), 'NC Governor')

    response = APIClient().get('/api/races/', {'scope': 'state'})

    assert response.status_code == 200
    assert response.json()['count'] == 0


@pytest.mark.django_db
def test_scope_zip_resolves_to_state_and_includes_national():
    national_election = _make_election('nat-3', level=Election.JurisdictionLevel.NATIONAL)
    nc_election = _make_election('nc-4', state='NC')
    ga_election = _make_election('ga-3', state='GA')
    national_race = _make_race(national_election, 'President')
    nc_race = _make_race(nc_election, 'NC Governor')
    ga_race = _make_race(ga_election, 'GA Governor')

    # ZIP 27601 is Raleigh, NC
    response = APIClient().get('/api/races/', {'scope': 'zip', 'zip': '27601'})

    assert response.status_code == 200
    ids = {r['id'] for r in response.json()['results']}
    assert national_race.id in ids
    assert nc_race.id in ids
    assert ga_race.id not in ids


@pytest.mark.django_db
def test_scope_zip_excludes_state_specific_races_from_national_election():
    """Races synced under a national election with a state-specific OCD ID must not
    appear for ZIP codes outside that state, but must appear for ZIP codes within it."""
    national_election = _make_election('nat-la', level=Election.JurisdictionLevel.NATIONAL)
    la_county_race = Race.objects.create(
        election=national_election,
        race_type=Race.RaceType.CANDIDATE,
        office_title='LA County Supervisor',
        jurisdiction='Los Angeles County',
        geography_scope='countywide',
        ocd_division_id='ocd-division/country:us/state:ca/county:los_angeles',
        source=Race.Source.CIVIC_API,
        race_status=Race.RaceStatus.ACTIVE,
        vote_method=Race.VoteMethod.SINGLE_CHOICE,
    )
    ca_senate_race = Race.objects.create(
        election=national_election,
        race_type=Race.RaceType.CANDIDATE,
        office_title='US Senate CA',
        jurisdiction='California',
        geography_scope='statewide',
        ocd_division_id='ocd-division/country:us/state:ca',
        source=Race.Source.CIVIC_API,
        race_status=Race.RaceStatus.ACTIVE,
        vote_method=Race.VoteMethod.SINGLE_CHOICE,
    )
    presidential_race = _make_race(national_election, 'President')  # ocd_division_id=''

    # ZIP 27601 is Raleigh, NC — LA county and CA senate races must not appear
    nc_response = APIClient().get('/api/races/', {'scope': 'zip', 'zip': '27601'})
    nc_ids = {r['id'] for r in nc_response.json()['results']}
    assert la_county_race.id not in nc_ids
    assert ca_senate_race.id not in nc_ids
    assert presidential_race.id in nc_ids

    # ZIP 90210 is Beverly Hills, CA — CA races must appear
    ca_response = APIClient().get('/api/races/', {'scope': 'zip', 'zip': '90210'})
    ca_ids = {r['id'] for r in ca_response.json()['results']}
    assert la_county_race.id in ca_ids
    assert ca_senate_race.id in ca_ids
    assert presidential_race.id in ca_ids


@pytest.mark.django_db
def test_scope_zip_invalid_zip_returns_empty():
    _make_race(_make_election('nc-5', state='NC'), 'NC Governor')

    response = APIClient().get('/api/races/', {'scope': 'zip', 'zip': '99999'})

    assert response.status_code == 200
    assert response.json()['count'] == 0


@pytest.mark.django_db
def test_scope_address_returns_empty():
    _make_race(_make_election('nc-6', state='NC'), 'NC Governor')

    response = APIClient().get('/api/races/', {'scope': 'address', 'address': '1 E Edenton St, Raleigh, NC'})

    assert response.status_code == 200
    assert response.json()['count'] == 0


@pytest.mark.django_db
def test_unknown_scope_returns_empty():
    _make_race(_make_election('nc-7', state='NC'), 'NC Governor')

    response = APIClient().get('/api/races/', {'scope': 'bogus'})

    assert response.status_code == 200
    assert response.json()['count'] == 0


@pytest.mark.django_db
def test_election_id_param_filters_by_election():
    election_a = _make_election('election-a', state='NC')
    election_b = _make_election('election-b', state='NC')
    race_a = _make_race(election_a, 'NC Senate')
    race_b = _make_race(election_b, 'NC House')

    response = APIClient().get('/api/races/', {'election_id': election_a.id})

    assert response.status_code == 200
    ids = {r['id'] for r in response.json()['results']}
    assert race_a.id in ids
    assert race_b.id not in ids


@pytest.mark.django_db
def test_backward_compat_state_param_without_scope():
    nc_election = _make_election('nc-bc', state='NC')
    ga_election = _make_election('ga-bc', state='GA')
    nc_race = _make_race(nc_election, 'NC Governor')
    ga_race = _make_race(ga_election, 'GA Governor')

    response = APIClient().get('/api/races/', {'state': 'NC'})

    assert response.status_code == 200
    ids = {r['id'] for r in response.json()['results']}
    assert nc_race.id in ids
    assert ga_race.id not in ids
