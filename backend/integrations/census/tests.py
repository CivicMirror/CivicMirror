from __future__ import annotations

from unittest.mock import patch

import pytest

from integrations.census.ocd_loader import find_ocd_id
from integrations.census.resolver import resolve_ocd_id, resolve_zip


@pytest.mark.django_db
@patch(
    'integrations.census.ocd_loader.load_ocd_divisions',
    return_value=[
        {'id': 'ocd-division/country:us/state:ca/cd:12', 'name': "California's 12th congressional district"},
    ],
)
def test_find_ocd_id_matches_congressional_district(mock_load_ocd_divisions):
    assert find_ocd_id('CA', 'cd', '12') == 'ocd-division/country:us/state:ca/cd:12'
    mock_load_ocd_divisions.assert_called_once()


@pytest.mark.django_db
@patch(
    'integrations.census.ocd_loader.load_ocd_divisions',
    return_value=[
        {'id': 'ocd-division/country:us/state:ca/cd:12', 'name': "California's 12th congressional district"},
    ],
)
def test_resolve_ocd_id_maps_house_office_type_to_congressional_ocd(mock_load_ocd_divisions):
    record = resolve_ocd_id('CA', 'H', '12')

    assert record is not None
    assert record.ocd_division_id == 'ocd-division/country:us/state:ca/cd:12'
    assert record.district_type == 'cd'
    assert record.district_number == '12'
    assert record.approximate is False
    mock_load_ocd_divisions.assert_called()


@pytest.mark.django_db
@patch(
    'integrations.census.ocd_loader.load_ocd_divisions',
    return_value=[
        {'id': 'ocd-division/country:us/state:ma/cd:7', 'name': "Massachusetts's 7th congressional district"},
        {'id': 'ocd-division/country:us/state:ma/sldu:norfolk_and_suffolk', 'name': 'Massachusetts Norfolk & Suffolk district'},
        {'id': 'ocd-division/country:us/state:ma/sldl:14th_suffolk', 'name': 'Massachusetts 14th Suffolk district'},
        {'id': 'ocd-division/country:us/state:ma/county:suffolk', 'name': 'Suffolk County'},
    ],
)
@patch(
    'integrations.census.resolver.CensusGeocoderClient.geocode_zip',
    return_value={
        'result': {
            'addressMatches': [
                {
                    'geographies': {
                        'States': [{'STUSAB': 'MA'}],
                        '119th Congressional Districts': [
                            {'GEOID': '2507', 'NAME': 'Congressional District 7', 'BASENAME': '7', 'CD119': '07'}
                        ],
                        '2024 State Legislative Districts - Upper': [
                            {'GEOID': '25D18', 'NAME': 'Norfolk and Suffolk District', 'BASENAME': 'Norfolk and Suffolk', 'SLDU': 'D18'}
                        ],
                        '2024 State Legislative Districts - Lower': [
                            {'GEOID': '25136', 'NAME': '14th Suffolk District', 'BASENAME': '14th Suffolk', 'SLDL': '136'}
                        ],
                        'Counties': [
                            {'GEOID': '25025', 'NAME': 'Suffolk County', 'BASENAME': 'Suffolk', 'STATE': '25', 'COUNTY': '025'}
                        ],
                    }
                }
            ]
        },
        'approximate': True,
    },
)
def test_resolve_zip_marks_district_records_as_approximate(mock_geocode_zip, mock_load_ocd_divisions):
    records = resolve_zip('02108')

    assert len(records) == 4
    assert {record.district_type for record in records} == {'cd', 'sldu', 'sldl', 'county'}
    assert all(record.approximate is True for record in records)
    mock_geocode_zip.assert_called_once_with('02108')
    mock_load_ocd_divisions.assert_called()
