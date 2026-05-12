from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from elections.models import Candidate, Election, MeasureOption, Race
from integrations.civic.cache import get_cache_key, get_race_ttl, races_are_fresh
from integrations.civic.tasks import sync_election_races, sync_elections
from ops.models import SyncLog


@pytest.mark.django_db
def test_cache_key_and_ttl_helpers_hide_plaintext_address():
    key = get_cache_key("123 Main St, Boston, MA 02110", "1001")
    assert "123 Main" not in key
    assert get_race_ttl(timezone.localdate() + timedelta(days=45)).total_seconds() == 48 * 3600


@pytest.mark.django_db
def test_races_are_fresh_uses_dynamic_ttl():
    election = Election.objects.create(
        name="Test Election",
        election_date=timezone.localdate() + timedelta(days=10),
        jurisdiction_level=Election.JurisdictionLevel.STATE,
        state="MA",
        source_id="sync-1",
        status=Election.Status.UPCOMING,
        last_synced_at=timezone.now(),
    )
    # Without any civic_api races, should not be considered fresh
    assert races_are_fresh(election) is False
    # Add a civic_api race — now it should be fresh
    Race.objects.create(
        election=election,
        race_type=Race.RaceType.CANDIDATE,
        office_title="Governor",
        jurisdiction="statewide",
        geography_scope="statewide",
        source=Race.Source.CIVIC_API,
        race_status=Race.RaceStatus.ACTIVE,
        vote_method=Race.VoteMethod.SINGLE_CHOICE,
    )
    assert races_are_fresh(election) is True


@pytest.mark.django_db
def test_sync_elections_creates_elections_and_queues_followups(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    with patch("integrations.civic.tasks.CivicAPIClient.list_elections", return_value=[{
        "source_id": "2000",
        "name": "Massachusetts General Election",
        "election_date": str(timezone.localdate() + timedelta(days=20)),
        "ocd_division_id": "ocd-division/country:us/state:ma",
    }]), patch("integrations.civic.tasks.sync_election_races.delay") as mocked_delay:
        result = sync_elections.apply().get()

    assert Election.objects.filter(source_id="2000").exists()
    assert result["created"] == 1
    assert mocked_delay.call_count >= 1


@pytest.mark.django_db
def test_sync_election_races_imports_candidate_and_measure_data(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    election = Election.objects.create(
        name="Massachusetts General Election",
        election_date=timezone.localdate() + timedelta(days=5),
        jurisdiction_level=Election.JurisdictionLevel.STATE,
        state="MA",
        source_id="3000",
        status=Election.Status.UPCOMING,
    )
    payload = {
        "contests": [
            {
                "type": "General",
                "office": "U.S. Senate",
                "district": {"name": "Massachusetts", "scope": "statewide", "id": "ocd-division/country:us/state:ma"},
                "candidates": [
                    {"name": "Alex Rivera", "party": "Independent"},
                    {"name": "Jordan Kim", "party": "Democratic"},
                ],
            },
            {
                "type": "Referendum",
                "referendumTitle": "Question 1",
                "district": {"name": "Massachusetts", "scope": "statewide", "id": "ocd-division/country:us/state:ma"},
            },
        ]
    }

    with patch("integrations.civic.tasks.CivicAPIClient.get_voter_info", return_value=payload):
        result = sync_election_races.apply(args=[election.id, "24 Beacon St, Boston, MA 02133", "MA-capital"]).get()

    assert result["created"] >= 5
    assert Race.objects.count() == 2
    assert Candidate.objects.count() == 2
    assert MeasureOption.objects.count() == 3
    assert SyncLog.objects.filter(task_name="sync_election_races", status=SyncLog.Status.COMPLETED).exists()
