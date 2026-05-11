from __future__ import annotations

from django.db.models import Count

from .models import MockVote


def build_choice_payload(*, candidate=None, measure_option=None):
    if candidate is not None:
        return {'type': 'candidate', 'id': candidate.id, 'label': candidate.name}
    if measure_option is not None:
        return {'type': 'measure_option', 'id': measure_option.id, 'label': measure_option.option_label}
    return None


def build_choice_payload_from_vote(vote: MockVote):
    return build_choice_payload(candidate=vote.candidate, measure_option=vote.measure_option)


def build_tally_payload(race, *, include_percent: bool = True, include_breakdowns: bool = True) -> dict:
    if race.race_type == race.RaceType.CANDIDATE:
        rows = [
            {
                'id': candidate.id,
                'label': candidate.name,
                'type': 'candidate',
                'count': candidate.vote_count,
            }
            for candidate in race.candidates.annotate(vote_count=Count('mock_votes')).order_by('-vote_count', 'name', 'id')
        ]
    else:
        rows = [
            {
                'id': option.id,
                'label': option.option_label,
                'type': 'measure_option',
                'count': option.vote_count,
            }
            for option in race.measure_options.annotate(vote_count=Count('mock_votes')).order_by('-vote_count', 'id')
        ]

    total_votes = sum(row['count'] for row in rows)
    options = []
    for row in rows:
        option = dict(row)
        if include_percent:
            option['percent'] = round((row['count'] / total_votes) * 100, 1) if total_votes else 0.0
        options.append(option)

    payload = {
        'race_id': race.id,
        'total_votes': total_votes,
        'options': options,
    }
    if include_breakdowns:
        payload['breakdowns'] = {'age_range': {}, 'country': {}, 'us_state': {}}
    return payload
