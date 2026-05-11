from datetime import date, timedelta

from celery import shared_task

from .models import Race


@shared_task
def auto_close_community_races():
    """Archive community races whose election_date + 14 days has passed."""
    cutoff = date.today() - timedelta(days=14)
    return Race.objects.filter(
        source=Race.Source.COMMUNITY,
        community_status=Race.CommunityStatus.ACTIVE,
        race_status=Race.RaceStatus.ACTIVE,
        election__election_date__lte=cutoff,
    ).update(race_status=Race.RaceStatus.ARCHIVED)
