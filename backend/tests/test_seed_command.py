import pytest
from django.core.management import call_command

from accounts.models import UserProfile
from elections.models import Candidate, Election, MeasureOption, Race
from voting.models import MockVote


@pytest.mark.django_db
def test_seed_dev_data_is_idempotent():
    call_command("seed_dev_data")
    first_counts = {
        "elections": Election.objects.count(),
        "races": Race.objects.count(),
        "candidates": Candidate.objects.count(),
        "measure_options": MeasureOption.objects.count(),
        "profiles": UserProfile.objects.count(),
        "votes": MockVote.objects.count(),
    }

    call_command("seed_dev_data")
    second_counts = {
        "elections": Election.objects.count(),
        "races": Race.objects.count(),
        "candidates": Candidate.objects.count(),
        "measure_options": MeasureOption.objects.count(),
        "profiles": UserProfile.objects.count(),
        "votes": MockVote.objects.count(),
    }

    assert first_counts == second_counts
    assert first_counts["elections"] == 2
    assert first_counts["races"] == 7
    assert first_counts["profiles"] == 3
    assert first_counts["votes"] == 20
