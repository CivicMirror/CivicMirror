import csv
import io
import logging
import re
import time

import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)

OCD_CSV_URL = 'https://raw.githubusercontent.com/opencivicdata/ocd-division-ids/master/identifiers/country-us.csv'
_CACHE_KEY = 'census:ocd_divisions'
_CACHE_TIMEOUT = 7 * 24 * 60 * 60


def _slug_token(value: str) -> str:
    normalized = (value or '').strip().lower().replace('&', ' and ')
    return re.sub(r'[^a-z0-9]+', '_', normalized).strip('_')


def _numeric_token(value: str) -> str:
    digits = ''.join(ch for ch in str(value or '') if ch.isdigit())
    if not digits:
        return ''
    return str(int(digits))


def load_ocd_divisions() -> list[dict]:
    """
    Download the CSV, parse it, return list of dicts with keys: id, name
    Cache in Django cache with key 'census:ocd_divisions' for 7 days.
    """
    cached = cache.get(_CACHE_KEY)
    if cached is not None:
        return cached

    for attempt in range(4):
        try:
            response = requests.get(OCD_CSV_URL, timeout=10)
        except requests.RequestException as exc:
            logger.warning('OCD divisions download failed on attempt %s: %s', attempt + 1, exc)
            if attempt >= 3:
                return []
            time.sleep(2 ** attempt)
            continue

        if response.status_code in {429, 503} or 500 <= response.status_code < 600:
            logger.warning('Retrying OCD division download status=%s attempt=%s', response.status_code, attempt + 1)
            if attempt >= 3:
                return []
            time.sleep(2 ** attempt)
            continue

        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning('Unable to fetch OCD divisions: %s', exc)
            return []

        rows = [
            {'id': row.get('id', '').strip(), 'name': row.get('name', '').strip()}
            for row in csv.DictReader(io.StringIO(response.text))
            if row.get('id')
        ]
        cache.set(_CACHE_KEY, rows, _CACHE_TIMEOUT)
        return rows

    return []


def get_ocd_name(ocd_id: str) -> str | None:
    for division in load_ocd_divisions():
        if division['id'] == ocd_id:
            return division.get('name') or None
    return None


def find_ocd_id(state: str, district_type: str, district_number: str = '') -> str | None:
    """
    Search loaded OCD divisions for a matching ID.
    district_type: 'cd' (congressional), 'sldu' (state upper), 'sldl' (state lower), 'county', 'place'
    Returns the OCD division ID string or None.
    """
    divisions = load_ocd_divisions()
    state_code = (state or '').strip().lower()

    if district_type == 'country':
        return next((division['id'] for division in divisions if division['id'] == 'ocd-division/country:us'), None)

    if district_type == 'state' and state_code:
        target = f'ocd-division/country:us/state:{state_code}'
        return next((division['id'] for division in divisions if division['id'] == target), None)

    if not state_code or not district_number:
        return None

    prefix = f'ocd-division/country:us/state:{state_code}/{district_type}:'
    candidates = [division for division in divisions if division['id'].startswith(prefix)]
    if not candidates:
        return None

    target_slug = _slug_token(district_number)
    target_number = _numeric_token(district_number)

    for division in candidates:
        suffix = division['id'][len(prefix):]
        suffix_slug = _slug_token(suffix)
        suffix_number = _numeric_token(suffix)
        name_slug = _slug_token(division.get('name', ''))

        if district_type == 'cd' and target_number and suffix_number == target_number:
            return division['id']

        if target_slug and (suffix_slug == target_slug or target_slug in name_slug or suffix_slug in target_slug):
            return division['id']

    return None
