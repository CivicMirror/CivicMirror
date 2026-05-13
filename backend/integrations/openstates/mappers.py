from __future__ import annotations

import re

from django.utils import timezone

STATE_RE = re.compile(r'state:([a-z]{2})', re.IGNORECASE)


def _extract_current_party(parties: list[dict] | None) -> str:
    for party in parties or []:
        if not isinstance(party, dict):
            continue
        if not party.get('end_date'):
            return party.get('name') or party.get('party') or ''
    return ''


def _extract_state(jurisdiction: str) -> str:
    match = STATE_RE.search(jurisdiction or '')
    return match.group(1).upper() if match else ''


def _first_value(items: list[dict] | None, key: str) -> str:
    for item in items or []:
        if isinstance(item, dict) and item.get(key):
            return item[key]
    return ''


def map_person(raw: dict) -> dict | None:
    current_role = raw.get('current_role') or {}
    if not current_role:
        return None

    jurisdiction = current_role.get('jurisdiction') or ''
    return {
        'openstates_person_id': str(raw.get('id') or ''),
        'party': _extract_current_party(raw.get('party')),
        'image_url': raw.get('image') or '',
        'website_url': _first_value(raw.get('links'), 'url'),
        'contact_phone': _first_value(raw.get('offices'), 'voice'),
        'contact_office': _first_value(raw.get('offices'), 'address'),
        'state': _extract_state(jurisdiction),
        'chamber': (current_role.get('org_classification') or '').lower(),
        'district': str(current_role.get('district') or ''),
        'display_name': (raw.get('name') or '').strip(),
        'source_metadata': {
            'openstates': {
                'person_id': str(raw.get('id') or ''),
                'jurisdiction': jurisdiction,
                'email': raw.get('email') or '',
                'last_synced': timezone.now().isoformat(),
            }
        },
    }
