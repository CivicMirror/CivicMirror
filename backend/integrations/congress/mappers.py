from __future__ import annotations

from datetime import date

from django.utils import timezone


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def map_legislator(raw: dict) -> dict | None:
    """
    Map a congress-legislators entry to a CivicMirror enrichment payload.

    Input structure:
      raw['id']:
        bioguide    → bioguide_id
        fec         → list of FEC IDs (use first if present)
        thomas, govtrack, opensecrets, etc. (ignore for now)

      raw['name']:
        official_full   → store in source_metadata, NOT as candidate name
        first, last     → for matching only

      raw['terms']:  list of term dicts; use terms[-1] (most recent)
        type: 'rep' or 'sen'
        state: 2-char
        district: int (House only)
        start, end: date strings
        party: party name
        phone: office phone
        address: office address
        url: official website

      raw['social']:  (may be missing)
        twitter, facebook, youtube → store in source_metadata

    Returns dict with keys:
      bioguide_id             (str)
      fec_candidate_id        (str, first FEC ID or '')
      party                   (str, from most recent term)
      incumbent               (True always — congress-legislators only has officeholders)
      contact_phone           (str)
      contact_office          (str)
      website_url             (str)
      state                   (str)
      office_type             ('H' for rep, 'S' for sen)
      district                (str, zero-padded e.g. '05', or '' for Senate)
      official_full_name      (str, for matching only)
      first_name, last_name   (str, for matching only)
      source_metadata: {
        'congress': {
          'official_full': ...,
          'twitter': ...,
          'facebook': ...,
          'youtube': ...,
          'bioguide_id': ...,
          'last_synced': <ISO datetime>
        }
      }

    Return None if terms is empty or most recent term has end date before today.
    (We only want current/active legislators.)
    """
    identifiers = raw.get('id') or {}
    names = raw.get('name') or {}
    terms = raw.get('terms') or []
    social = raw.get('social') or {}
    if not terms:
        return None

    latest_term = terms[-1] or {}
    end_date = _parse_date(latest_term.get('end', ''))
    if end_date and end_date < timezone.localdate():
        return None

    office_type = {'rep': 'H', 'sen': 'S'}.get((latest_term.get('type') or '').lower())
    if not office_type:
        return None

    fec_ids = identifiers.get('fec') or []
    if isinstance(fec_ids, str):
        fec_ids = [fec_ids]

    first_name = (names.get('first') or '').strip()
    last_name = (names.get('last') or '').strip()
    official_full_name = (names.get('official_full') or f'{first_name} {last_name}').strip()
    district = ''
    if office_type == 'H' and latest_term.get('district') not in (None, ''):
        district = str(latest_term.get('district')).zfill(2)

    bioguide_id = str(identifiers.get('bioguide') or '').strip()
    now = timezone.now().isoformat()
    return {
        'bioguide_id': bioguide_id,
        'fec_candidate_id': str(fec_ids[0]).strip() if fec_ids else '',
        'party': (latest_term.get('party') or '').strip(),
        'incumbent': True,
        'contact_phone': (latest_term.get('phone') or '').strip(),
        'contact_office': (latest_term.get('address') or '').strip(),
        'website_url': (latest_term.get('url') or '').strip(),
        'state': (latest_term.get('state') or '').upper(),
        'office_type': office_type,
        'district': district,
        'official_full_name': official_full_name,
        'first_name': first_name,
        'last_name': last_name,
        'source_metadata': {
            'congress': {
                'official_full': official_full_name,
                'twitter': (social.get('twitter') or '').strip(),
                'facebook': (social.get('facebook') or '').strip(),
                'youtube': (social.get('youtube') or '').strip(),
                'bioguide_id': bioguide_id,
                'last_synced': now,
            }
        },
    }
