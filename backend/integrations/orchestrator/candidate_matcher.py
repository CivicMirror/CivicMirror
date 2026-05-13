from __future__ import annotations

import re

from elections.models import Candidate, Race

from .enrichment import get_fields_to_update, merge_source_metadata

# Field-level source priority
FIELD_PRIORITY = {
    'party': ['civic_api', 'fec', 'congress', 'openstates', 'openelections'],
    'incumbent': ['civic_api', 'congress', 'openstates', 'openelections'],
    'image_url': ['civic_api', 'openstates', 'openelections'],
    'website_url': ['civic_api', 'congress', 'openstates', 'openelections'],
    'description': ['civic_api', 'congress', 'openelections'],
    'contact_phone': ['congress', 'openstates', 'openelections'],
    'contact_office': ['congress', 'openstates', 'openelections'],
}

# Never overwrite these fields from enrichment sources:
IMMUTABLE_FROM_ENRICHMENT = {'name'}
CONGRESSIONAL_DISTRICT_RE = re.compile(r'(?:/cd:|district\s+)(\d+)', re.IGNORECASE)


class CandidateMatcher:
    """
    Match tiers (in order):
      1. External ID match: fec_candidate_id, bioguide_id, openstates_person_id
      2. Cross-reference: congress-legislators provides FEC IDs → match by fec_candidate_id
      3. Normalized name within race
      4. Normalized name + state + office type (cross-race enrichment)
    """

    external_id_fields = ('fec_candidate_id', 'bioguide_id', 'openstates_person_id')

    def enrich(
        self,
        race: Race | None,
        source: str,
        external_id: str,
        enrichment_payload: dict,
    ) -> tuple['Candidate | None', str]:
        """
        enrichment_payload keys:
          - name (str, optional)
          - official_full_name (str, optional)
          - first_name / last_name (str, optional)
          - party (str, optional)
          - incumbent (bool, optional)
          - image_url (str, optional)
          - website_url (str, optional)
          - description (str, optional)
          - contact_phone (str, optional)
          - contact_office (str, optional)
          - fec_candidate_id (str, optional)
          - bioguide_id (str, optional)
          - openstates_person_id (str, optional)
          - source_metadata (dict, optional) — stored under source key in Candidate.source_metadata

        Returns (candidate, action) where action is:
          'enriched'   — match found, one or more fields updated
          'no_match'   — no candidate found for this source record
          'ambiguous'  — multiple possible matches (log, skip)
          'skipped'    — match found but no fields changed

        Rules:
          - NEVER update Candidate.name from enrichment sources
          - Only update a field if current value is blank/None OR source has higher priority
          - Merge source_metadata by key (never replace whole dict)
          - Set external ID fields (fec_candidate_id etc.) on first match only
        """
        candidate, ambiguous = self._find_candidate(race, enrichment_payload)
        if ambiguous:
            return None, 'ambiguous'
        if candidate is None:
            return None, 'no_match'

        updates = get_fields_to_update(candidate, source, enrichment_payload)
        metadata_updates = {'external_id': str(external_id)}
        source_metadata_payload = enrichment_payload.get('source_metadata') or {}
        if isinstance(source_metadata_payload.get(source), dict):
            metadata_updates.update(source_metadata_payload[source])
        else:
            metadata_updates.update(source_metadata_payload)
        merged_source_metadata = merge_source_metadata(candidate.source_metadata or {}, source, metadata_updates)

        field_source_metadata = updates.pop('source_metadata', None)
        if field_source_metadata and field_source_metadata.get('_field_sources'):
            merged_source_metadata['_field_sources'] = field_source_metadata['_field_sources']

        for field in self.external_id_fields:
            incoming_value = enrichment_payload.get(field)
            if incoming_value and not getattr(candidate, field):
                updates[field] = incoming_value

        if merged_source_metadata != (candidate.source_metadata or {}):
            updates['source_metadata'] = merged_source_metadata

        if not updates:
            return candidate, 'skipped'

        for field, value in updates.items():
            setattr(candidate, field, value)
        candidate.save(update_fields=list(updates.keys()))
        return candidate, 'enriched'

    def _find_candidate(self, race: Race | None, payload: dict) -> tuple[Candidate | None, bool]:
        candidate, ambiguous = self._match_by_external_ids(payload)
        if candidate is not None or ambiguous:
            return candidate, ambiguous

        candidate, ambiguous = self._match_by_cross_reference(payload)
        if candidate is not None or ambiguous:
            return candidate, ambiguous

        name = self._payload_name(payload)
        if race is not None:
            candidate, ambiguous = self._match_by_name_within_race(race, name)
            if candidate is not None or ambiguous:
                return candidate, ambiguous
            return self._match_cross_race(race, name)

        return self._match_cross_race_from_payload(payload, name)

    def _match_by_external_ids(self, payload: dict) -> tuple[Candidate | None, bool]:
        for field in self.external_id_fields:
            value = payload.get(field)
            if not value:
                continue
            matches = list(Candidate.objects.filter(**{field: value})[:2])
            if len(matches) == 1:
                return matches[0], False
            if len(matches) > 1:
                return None, True
        return None, False

    def _match_by_cross_reference(self, payload: dict) -> tuple[Candidate | None, bool]:
        fec_ids = payload.get('fec_candidate_ids') or payload.get('fec_ids') or []
        if isinstance(fec_ids, str):
            fec_ids = [fec_ids]
        matches = list(Candidate.objects.filter(fec_candidate_id__in=fec_ids).distinct()[:2])
        if len(matches) == 1:
            return matches[0], False
        if len(matches) > 1:
            return None, True
        return None, False

    def _match_by_name_within_race(self, race: Race, name: str) -> tuple[Candidate | None, bool]:
        normalized_name = self._normalize(name)
        if not normalized_name:
            return None, False
        matches = [candidate for candidate in race.candidates.all() if self._normalize(candidate.name) == normalized_name]
        if len(matches) == 1:
            return matches[0], False
        if len(matches) > 1:
            return None, True
        return None, False

    def _match_cross_race(self, race: Race, name: str) -> tuple[Candidate | None, bool]:
        normalized_name = self._normalize(name)
        state = race.election.state
        office_type = race.normalized_office_title or self._normalize(race.office_title)
        if not normalized_name or not state or not office_type:
            return None, False

        matches = [
            candidate
            for candidate in Candidate.objects.filter(
                race__election__state=state,
                race__normalized_office_title=office_type,
            ).select_related('race', 'race__election')
            if self._normalize(candidate.name) == normalized_name
        ]
        if len(matches) == 1:
            return matches[0], False
        if len(matches) > 1:
            return None, True
        return None, False

    # Keywords used to infer state legislature chamber from race title
    _UPPER_CHAMBER_KEYWORDS = frozenset({'senate'})
    _LOWER_CHAMBER_KEYWORDS = frozenset({'house', 'assembly', 'delegate', 'representative'})

    def _match_cross_race_from_payload(self, payload: dict, name: str) -> tuple[Candidate | None, bool]:
        normalized_name = self._normalize(name)
        state = (payload.get('state') or '').upper()
        if not normalized_name or not state:
            return None, False

        office_type = (payload.get('office_type') or '').upper()
        district = self._normalize_district(payload.get('district'))

        # Tier 1: congressional office type (H / S)
        if office_type in {'H', 'S'}:
            matches = [
                candidate
                for candidate in Candidate.objects.filter(race__election__state=state).select_related('race', 'race__election')
                if self._normalize(candidate.name) == normalized_name
                and self._race_matches_congressional_office(candidate.race, office_type, district)
            ]
            if len(matches) == 1:
                return matches[0], False
            if len(matches) > 1:
                return None, True
            return None, False

        # Tier 2: state legislature chamber (upper / lower)
        chamber = (payload.get('chamber') or '').lower()
        if chamber in {'upper', 'lower'}:
            keywords = self._UPPER_CHAMBER_KEYWORDS if chamber == 'upper' else self._LOWER_CHAMBER_KEYWORDS
            candidates = list(
                Candidate.objects.filter(race__election__state=state).select_related('race', 'race__election')
            )
            matches = [
                c for c in candidates
                if self._normalize(c.name) == normalized_name
                and any(
                    kw in self._normalize(c.race.normalized_office_title or c.race.office_title)
                    for kw in keywords
                )
            ]
            if len(matches) == 1:
                return matches[0], False
            if len(matches) > 1:
                return None, True

        return None, False

    def _race_matches_congressional_office(self, race: Race, office_type: str, district: str) -> bool:
        race_office_type = self._infer_congressional_office_type(race)
        if race_office_type != office_type:
            return False
        if office_type != 'H':
            return True
        return self._extract_district_number(race) == district

    def _infer_congressional_office_type(self, race: Race) -> str:
        normalized_title = self._normalize(race.normalized_office_title or race.office_title)
        ocd_division_id = (race.ocd_division_id or '').lower()
        if '/cd:' in ocd_division_id:
            return 'H'
        if 'u.s. senate' in normalized_title or 'us senate' in normalized_title or 'united states senate' in normalized_title:
            return 'S'
        if any(token in normalized_title for token in ('u.s. house', 'us house', 'united states house', 'representative')):
            return 'H'
        return ''

    def _extract_district_number(self, race: Race) -> str:
        for value in (race.ocd_division_id, race.office_title, race.jurisdiction):
            match = CONGRESSIONAL_DISTRICT_RE.search(value or '')
            if match:
                return self._normalize_district(match.group(1))
        return ''

    def _payload_name(self, payload: dict) -> str:
        if payload.get('name'):
            return str(payload['name'])
        if payload.get('official_full_name'):
            return str(payload['official_full_name'])
        first_name = str(payload.get('first_name') or '').strip()
        last_name = str(payload.get('last_name') or '').strip()
        return f'{first_name} {last_name}'.strip()

    @staticmethod
    def _normalize_district(value) -> str:
        digits = ''.join(ch for ch in str(value or '') if ch.isdigit())
        return digits.lstrip('0') or ('0' if digits else '')

    @staticmethod
    def _normalize(value: str) -> str:
        return ' '.join((value or '').strip().lower().split())
