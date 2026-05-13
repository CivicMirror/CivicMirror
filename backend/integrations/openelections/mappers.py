from __future__ import annotations

from pathlib import Path


def parse_result_file_metadata(file_path: str) -> tuple[str, str]:
    filename = Path(file_path).name
    stem = filename.rsplit('.', 1)[0]
    parts = stem.split('__')
    if len(parts) < 4:
        raise ValueError(f'Invalid OpenElections filename: {file_path}')
    raw_date = parts[0]
    if len(raw_date) != 8 or not raw_date.isdigit():
        raise ValueError(f'Invalid OpenElections filename date: {file_path}')
    election_date = f'{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}'
    office = parts[3].strip().lower()
    return election_date, office


def map_result_row(row: dict, state: str, election_date: str, office: str) -> dict | None:
    candidate_name = str(row.get('candidate') or '').strip()
    raw_votes = row.get('votes')
    if not candidate_name:
        return None
    if raw_votes in (None, ''):
        return None

    try:
        votes = int(str(raw_votes).replace(',', '').strip())
    except (TypeError, ValueError):
        return None

    return {
        'candidate_name': candidate_name,
        'party': str(row.get('party') or '').strip() or None,
        'office': str(row.get('office') or office or '').strip() or office,
        'district': str(row.get('district') or '').strip() or None,
        'state': (state or '').upper(),
        'election_date': election_date,
        'votes': votes,
        'winner': _coerce_winner(row.get('winner')),
        'raw_county': str(row.get('county') or '').strip() or None,
        'raw_precinct': str(row.get('precinct') or '').strip() or None,
    }


def _coerce_winner(value) -> bool:
    normalized = str(value or '').strip().lower()
    return normalized in {'1', 'true', 't', 'yes', 'y', 'winner'}
