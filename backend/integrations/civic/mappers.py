from datetime import date, datetime, time, timedelta
import re

from django.utils import timezone

from elections.models import Candidate, Election, Race

STATE_RE = re.compile(r"state:([a-z]{2})", re.IGNORECASE)


def build_canonical_key(source, election_source_id, normalized_title, ocd_id, race_type, election_date):
    parts = [source, election_source_id, normalized_title, ocd_id or "NO_OCD", race_type, str(election_date)]
    return ":".join(parts)


def normalize_office_title(title: str) -> str:
    return " ".join(title.strip().lower().split())


def parse_state_from_ocd(ocd_division_id: str) -> str | None:
    if not ocd_division_id:
        return None
    match = STATE_RE.search(ocd_division_id)
    return match.group(1).upper() if match else None


def parse_jurisdiction_level(ocd_division_id: str) -> str:
    lowered = (ocd_division_id or "").lower()
    if "state:" not in lowered:
        return Election.JurisdictionLevel.NATIONAL
    if any(part in lowered for part in ("county:", "place:", "district:", "city:")):
        return Election.JurisdictionLevel.LOCAL
    return Election.JurisdictionLevel.STATE


def infer_election_status(election_date: date) -> str:
    today = timezone.localdate()
    if election_date > today:
        return Election.Status.UPCOMING
    if election_date == today:
        return Election.Status.ACTIVE
    if election_date >= today - timedelta(days=30):
        return Election.Status.RESULTS_PENDING
    return Election.Status.ARCHIVED


def map_election_payload(payload: dict) -> dict:
    election_date = payload["election_date"]
    if isinstance(election_date, str):
        election_date = date.fromisoformat(election_date)
    ocd_division_id = payload.get("ocd_division_id", "")
    return {
        "source_id": str(payload["source_id"]),
        "name": payload["name"],
        "election_date": election_date,
        "jurisdiction_level": parse_jurisdiction_level(ocd_division_id),
        "state": parse_state_from_ocd(ocd_division_id),
        "status": infer_election_status(election_date),
    }


def infer_race_type(contest: dict) -> str:
    if (contest.get("type") or "").lower() == "referendum" or contest.get("referendumTitle"):
        return Race.RaceType.MEASURE
    return Race.RaceType.CANDIDATE


def extract_contest_title(contest: dict) -> str:
    office = (
        contest.get("office")
        or contest.get("ballotTitle")
        or contest.get("referendumTitle")
        or contest.get("referendumSubtitle")
    )
    if not office:
        return "Untitled Contest"
    parties = contest.get("primaryParties") or []
    if parties and (contest.get("type") or "").lower() == "primary":
        party_label = " / ".join(p.title() for p in parties)
        return f"{office} \u2014 {party_label} Primary"
    return office


def extract_jurisdiction(contest: dict) -> str:
    district = contest.get("district") or {}
    level = contest.get("level") or []
    if isinstance(level, list) and level:
        level_value = level[0]
    else:
        level_value = level
    return district.get("name") or level_value or "Unknown jurisdiction"


def extract_geography_scope(contest: dict) -> str:
    district = contest.get("district") or {}
    return district.get("scope") or "district"


def default_voting_window(election_date: date):
    opens = timezone.make_aware(datetime.combine(election_date, time.min))
    closes = timezone.make_aware(datetime.combine(election_date, time(23, 59, 59)))
    return opens, closes


def map_contest_to_race_defaults(election: Election, contest: dict) -> dict:
    race_type = infer_race_type(contest)
    office_title = extract_contest_title(contest)
    normalized_title = normalize_office_title(office_title)
    ocd_id = contest.get("district", {}).get("id") or contest.get("officeDivisionId") or election.state or ""
    opens, closes = default_voting_window(election.election_date)
    vote_method = Race.VoteMethod.YES_NO if race_type == Race.RaceType.MEASURE else Race.VoteMethod.SINGLE_CHOICE
    return {
        "race_type": race_type,
        "ballot_type": contest.get("type", ""),
        "office_title": office_title,
        "jurisdiction": extract_jurisdiction(contest),
        "geography_scope": extract_geography_scope(contest),
        "voting_opens": opens,
        "voting_closes": closes,
        "certification_status": Race.CertificationStatus.UPCOMING if election.status in {Election.Status.UPCOMING, Election.Status.ACTIVE} else Race.CertificationStatus.RESULTS_PENDING,
        "source": Race.Source.CIVIC_API,
        "race_status": Race.RaceStatus.ACTIVE,
        "vote_method": vote_method,
        "max_selections": 1,
        "ocd_division_id": ocd_id,
        "normalized_office_title": normalized_title,
        "canonical_key": build_canonical_key(
            Race.Source.CIVIC_API,
            election.source_id,
            normalized_title,
            ocd_id,
            race_type,
            election.election_date,
        ),
    }


def map_candidate_defaults(candidate_payload: dict) -> dict:
    website_url = ""
    if candidate_payload.get("urls"):
        website_url = candidate_payload["urls"][0]
    return {
        "party": candidate_payload.get("party", ""),
        "incumbent": bool(candidate_payload.get("incumbent", False)),
        "candidate_status": Candidate.CandidateStatus.RUNNING,
        "description": candidate_payload.get("biography", "")[:2000],
        "image_url": candidate_payload.get("photoUrl", ""),
        "website_url": website_url,
    }


def measure_option_labels() -> list[str]:
    return ["Yes", "No", "Abstain"]
