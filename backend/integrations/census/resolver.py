import logging

from elections.models import DistrictRecord

from .client import CensusGeocoderClient
from .ocd_loader import find_ocd_id, get_ocd_name

logger = logging.getLogger(__name__)


def _first_geography_rows(geographies: dict, label_fragment: str) -> list[dict]:
    for label, rows in geographies.items():
        if label_fragment in label:
            return rows
    return []


def _congressional_number(row: dict) -> str:
    for key, value in row.items():
        if key.startswith('CD') and key != 'CDSESSN' and value:
            try:
                return str(int(str(value)))
            except ValueError:
                return str(value)
    return str(row.get('BASENAME', '')).strip()


def _extract_districts(payload: dict | None, state_hint: str = '') -> list[dict]:
    if not payload:
        return []

    matches = payload.get('result', {}).get('addressMatches') or []
    if not matches:
        return []

    geographies = matches[0].get('geographies', {})
    state_rows = geographies.get('States') or []
    state_code = (state_rows[0].get('STUSAB') if state_rows else state_hint) or state_hint
    state_code = state_code.upper()

    districts: list[dict] = []

    congressional_rows = _first_geography_rows(geographies, 'Congressional Districts')
    if congressional_rows:
        row = congressional_rows[0]
        districts.append(
            {
                'state': state_code,
                'district_type': 'cd',
                'district_number': _congressional_number(row),
                'name': row.get('NAME', ''),
                'fips_code': row.get('GEOID', ''),
            }
        )

    upper_rows = _first_geography_rows(geographies, 'State Legislative Districts - Upper')
    if upper_rows:
        row = upper_rows[0]
        districts.append(
            {
                'state': state_code,
                'district_type': 'sldu',
                'district_number': row.get('BASENAME') or row.get('SLDU', ''),
                'name': row.get('NAME', ''),
                'fips_code': row.get('GEOID', ''),
            }
        )

    lower_rows = _first_geography_rows(geographies, 'State Legislative Districts - Lower')
    if lower_rows:
        row = lower_rows[0]
        districts.append(
            {
                'state': state_code,
                'district_type': 'sldl',
                'district_number': row.get('BASENAME') or row.get('SLDL', ''),
                'name': row.get('NAME', ''),
                'fips_code': row.get('GEOID', ''),
            }
        )

    county_rows = geographies.get('Counties') or []
    if county_rows:
        row = county_rows[0]
        districts.append(
            {
                'state': state_code,
                'district_type': 'county',
                'district_number': row.get('BASENAME') or row.get('NAME', ''),
                'name': row.get('NAME', ''),
                'fips_code': row.get('GEOID') or f"{row.get('STATE', '')}{row.get('COUNTY', '')}",
            }
        )

    return districts


def _upsert_district_record(district: dict, approximate: bool) -> DistrictRecord | None:
    ocd_id = find_ocd_id(district['state'], district['district_type'], district['district_number'])
    if not ocd_id:
        logger.warning(
            'No OCD division found for state=%s type=%s district=%s',
            district['state'],
            district['district_type'],
            district['district_number'],
        )
        return None

    defaults = {
        'state': district['state'],
        'district_type': district['district_type'],
        'district_number': str(district['district_number']),
        'name': get_ocd_name(ocd_id) or district['name'] or ocd_id,
        'fips_code': district.get('fips_code', ''),
        'approximate': approximate,
    }
    record, created = DistrictRecord.objects.get_or_create(
        ocd_division_id=ocd_id,
        election_year_valid=None,
        defaults=defaults,
    )
    if created:
        return record

    changed_fields = []
    for field, value in defaults.items():
        if getattr(record, field) != value:
            setattr(record, field, value)
            changed_fields.append(field)

    if changed_fields:
        record.save(update_fields=changed_fields)
    return record


def _resolve_payload(payload: dict | None, *, state_hint: str = '', approximate: bool = False) -> list[DistrictRecord]:
    records = []
    seen_ids = set()
    for district in _extract_districts(payload, state_hint=state_hint):
        record = _upsert_district_record(district, approximate=approximate)
        if record and record.ocd_division_id not in seen_ids:
            records.append(record)
            seen_ids.add(record.ocd_division_id)
    return records


def resolve_address(street: str, city: str, state: str, zip_code: str = '') -> list[DistrictRecord]:
    """
    Geocode address → extract congressional district, state leg districts, county.
    For each district found:
      - Build OCD division ID using ocd_loader.find_ocd_id()
      - get_or_create DistrictRecord
    Returns list of DistrictRecord instances (may be empty on geocoding failure).
    """
    client = CensusGeocoderClient()
    payload = client.geocode_address(street=street, city=city, state=state, zip_code=zip_code)
    return _resolve_payload(payload, state_hint=state, approximate=False)


def resolve_zip(zip_code: str) -> list[DistrictRecord]:
    """
    Approximate district resolution from ZIP code.
    Same flow as resolve_address but:
      - Sets DistrictRecord.approximate = True
      - Logs a warning that results are approximate
    """
    logger.warning('Resolving districts from ZIP code %s using approximate Census geocoding.', zip_code)
    client = CensusGeocoderClient()
    payload = client.geocode_zip(zip_code)
    return _resolve_payload(payload, approximate=True)


def resolve_ocd_id(state: str, office_type: str, district: str = '') -> DistrictRecord | None:
    """
    Direct OCD ID lookup without geocoding.
    office_type: 'H' (House), 'S' (Senate), 'P' (President), 'state_upper', 'state_lower'
    Maps office_type to OCD district_type, calls find_ocd_id, get_or_create DistrictRecord.
    Returns DistrictRecord or None.
    """
    state_code = (state or '').upper()
    office_mapping = {
        'H': ('cd', district, state_code),
        'S': ('state', '', state_code),
        'P': ('country', '', 'US'),
        'state_upper': ('sldu', district, state_code),
        'state_lower': ('sldl', district, state_code),
    }
    if office_type not in office_mapping:
        return None

    district_type, district_number, record_state = office_mapping[office_type]
    ocd_id = find_ocd_id(record_state, district_type, district_number)
    if not ocd_id:
        return None

    record_name = get_ocd_name(ocd_id) or ocd_id
    record, created = DistrictRecord.objects.get_or_create(
        ocd_division_id=ocd_id,
        election_year_valid=None,
        defaults={
            'state': record_state,
            'district_type': district_type,
            'district_number': str(district_number),
            'name': record_name,
            'approximate': False,
        },
    )
    if created:
        return record

    changed_fields = []
    desired_values = {
        'state': record_state,
        'district_type': district_type,
        'district_number': str(district_number),
        'name': record_name,
        'approximate': False,
    }
    for field, value in desired_values.items():
        if getattr(record, field) != value:
            setattr(record, field, value)
            changed_fields.append(field)

    if changed_fields:
        record.save(update_fields=changed_fields)
    return record
