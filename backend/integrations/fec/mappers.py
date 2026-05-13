from datetime import date


def _normalize_text(value: str) -> str:
    return ' '.join((value or '').strip().lower().split())


def map_candidate(raw: dict) -> dict | None:
    """
    Map FEC candidate dict to CivicMirror enrichment payload.
    FEC fields of interest:
      candidate_id        → fec_candidate_id
      name                → (store in source_metadata only; never overwrite Candidate.name)
      office              → office_type ('H', 'S', 'P')
      office_full         → used for race matching
      state               → state
      district            → district number string e.g. '05'
      party_full          → party
      incumbent_challenge_full → 'Incumbent', 'Challenger', 'Open seat'
      election_years      → list of ints, pick the one matching requested cycle
      candidate_status    → 'C' (current), 'F' (future), 'N' (not yet), 'P' (prior)

    Returns dict with keys:
      fec_candidate_id, office_type, state, district, party, incumbent,
      normalized_office_title, source_metadata (with 'fec' sub-key containing raw fields)

    'incumbent' = True only if incumbent_challenge_full == 'Incumbent'
    'normalized_office_title' = normalize the office_full string (lowercase, strip, collapse spaces)
    Skip (return None) if candidate_status not in ('C', 'F')
    """
        
    candidate_status = (raw.get('candidate_status') or '').strip().upper()
    if candidate_status not in {'C', 'F'}:
        return None

    district = raw.get('district')
    district_value = str(district).strip() if district not in (None, '') else ''
    state = (raw.get('state') or '').strip().upper() or None

    source_fields = {
        'candidate_id': raw.get('candidate_id'),
        'name': (raw.get('name') or '').strip(),
        'office': raw.get('office'),
        'office_full': raw.get('office_full'),
        'state': state,
        'district': district_value,
        'party_full': raw.get('party_full'),
        'incumbent_challenge_full': raw.get('incumbent_challenge_full'),
        'election_years': raw.get('election_years') or [],
        'candidate_status': candidate_status,
    }

    return {
        'fec_candidate_id': str(raw.get('candidate_id') or '').strip(),
        'office_type': (raw.get('office') or '').strip(),
        'state': state,
        'district': district_value,
        'party': (raw.get('party_full') or '').strip(),
        'incumbent': (raw.get('incumbent_challenge_full') or '').strip() == 'Incumbent',
        'normalized_office_title': _normalize_text(raw.get('office_full') or ''),
        'source_metadata': {'fec': source_fields},
    }


def fec_office_to_ocd_type(office: str) -> str:
    """
    Map FEC office code to OCD district type for census resolver.
    'H' → 'cd'  (congressional district)
    'S' → 's'   (statewide/Senate)
    'P' → ''    (national/President)
    """
    return {
        'H': 'cd',
        'S': 's',
        'P': '',
    }.get((office or '').strip().upper(), '')


def current_cycle() -> int:
    """Return the current federal election cycle year (even years only)."""
    year = date.today().year
    return year if year % 2 == 0 else year + 1
