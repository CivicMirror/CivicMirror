import hashlib
from datetime import date, timedelta

from django.core.cache import cache
from django.utils import timezone

from elections.models import Election



def get_race_ttl(election_date: date) -> timedelta:
    days_until = (election_date - date.today()).days
    if days_until > 30:
        return timedelta(hours=48)
    if days_until > 7:
        return timedelta(hours=24)
    if days_until > 1:
        return timedelta(hours=6)
    return timedelta(hours=1)



def get_cache_key(address: str, election_id: str) -> str:
    raw = f"{address.strip().lower()}:{election_id}"
    return f"civic:voter_info:{hashlib.sha256(raw.encode()).hexdigest()[:16]}"



def get_cached_voter_info(address: str, election_id: str):
    return cache.get(get_cache_key(address, election_id))



def set_cached_voter_info(address: str, election_id: str, data: dict):
    cache.set(get_cache_key(address, election_id), data, timeout=3600)



def races_are_fresh(election: Election) -> bool:
    if not election.last_synced_at:
        return False
    if not election.races.filter(source='civic_api').exists():
        return False
    ttl = get_race_ttl(election.election_date)
    return (timezone.now() - election.last_synced_at) < ttl
