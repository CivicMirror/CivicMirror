from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Case, IntegerField, Q, When

from elections.models import DistrictRecord, Election, Race

from .exceptions import AmbiguousMatchError, NoRaceFoundError

# Source priority order (lower index = higher priority)
SOURCE_PRIORITY = ['civic_api', 'medsl', 'openelections', 'fec', 'openstates', 'congress']

PRIMARY_SOURCES = {'civic_api', 'medsl'}
ENRICHMENT_SOURCES = {'fec', 'openstates', 'congress', 'openelections'}


class RaceMatcher:
    """
    Resolves whether an incoming raw race record matches an existing Race.
    Match tiers (in order):
      1. Exact canonical_key match (same-source records)
      2. OCD division ID + normalized_office_title + election date
      3. state + normalized_office_title + district + election date
      4. normalized_office_title + state + approximate date range (±30 days) → LOW confidence
    """

    def find_or_create(
        self,
        source: str,
        external_id: str,
        normalized_payload: dict,
        district_records: list = None,
    ) -> tuple[Race, bool]:
        """
        normalized_payload keys:
          - canonical_key (str, optional) — use for tier-1 match
          - ocd_division_id (str)
          - normalized_office_title (str)
          - election_date (date)
          - state (str, 2-char)
          - office_title (str)
          - race_type (str)
          - geography_scope (str)
          - election_id (int, optional) — FK to existing Election if known
          - source (str) — the source creating/matching this race

        Returns (race, created).
        Sets race.match_confidence appropriately.
        If confidence is 'low' or 'flagged', sets race.race_status = 'pending_review'.
        Enrichment-only sources (fec, congress, openstates, openelections) raise NoRaceFoundError
          instead of creating a new Race when no match is found.
        """
        district_records = district_records or []
        payload = dict(normalized_payload)
        election_date = self._coerce_date(payload['election_date'])
        normalized_title = payload.get('normalized_office_title') or self._normalize(payload.get('office_title', ''))
        race_type = payload.get('race_type', Race.RaceType.CANDIDATE)
        base_filters = {
            'normalized_office_title': normalized_title,
            'race_type': race_type,
        }

        canonical_key = payload.get('canonical_key')
        if canonical_key:
            race = Race.objects.filter(canonical_key=canonical_key).select_related('election').first()
            if race is not None:
                return self._apply_match(race, source, external_id, Race.MatchConfidence.VERIFIED), False

        ocd_division_id = payload.get('ocd_division_id')
        if ocd_division_id:
            tier_two_query = Race.objects.filter(
                **base_filters,
                ocd_division_id=ocd_division_id,
                election__election_date=election_date,
            ).select_related('election')
            race = self._select_match(tier_two_query)
            if race is not None:
                return self._apply_match(race, source, external_id, Race.MatchConfidence.HIGH), False

        state = (payload.get('state') or '').upper()
        district_ocd_ids, district_names = self._resolve_district_candidates(state, payload, district_records, election_date.year)
        if state and (district_ocd_ids or district_names):
            tier_three_query = Race.objects.filter(
                **base_filters,
                election__state=state,
                election__election_date=election_date,
            ).select_related('election')
            district_filter = Q()
            if district_ocd_ids:
                district_filter |= Q(ocd_division_id__in=district_ocd_ids)
            for name in district_names:
                district_filter |= Q(jurisdiction__iexact=name)
            race = self._select_match(tier_three_query.filter(district_filter))
            if race is not None:
                return self._apply_match(race, source, external_id, Race.MatchConfidence.MEDIUM), False

        if state:
            date_range = (election_date - timedelta(days=30), election_date + timedelta(days=30))
            tier_four_query = Race.objects.filter(
                **base_filters,
                election__state=state,
                election__election_date__range=date_range,
            ).select_related('election')
            race = self._select_match(tier_four_query)
            if race is not None:
                return self._apply_match(race, source, external_id, Race.MatchConfidence.LOW), False

        if source in ENRICHMENT_SOURCES:
            raise NoRaceFoundError(f'No race found for {source}:{external_id}')

        election = self._resolve_election(source, external_id, payload, election_date)
        race_lookup = {'canonical_key': canonical_key} if canonical_key else {
            'election': election,
            'normalized_office_title': normalized_title,
            'ocd_division_id': ocd_division_id or '',
            'source': source,
            'race_type': race_type,
        }
        defaults = {
            'election': election,
            'race_type': race_type,
            'office_title': payload.get('office_title') or normalized_title.title(),
            'jurisdiction': payload.get('jurisdiction') or payload.get('state') or 'Unknown jurisdiction',
            'geography_scope': payload.get('geography_scope') or 'district',
            'source': source,
            'ocd_division_id': ocd_division_id or '',
            'normalized_office_title': normalized_title,
            'canonical_key': canonical_key,
            'match_confidence': Race.MatchConfidence.VERIFIED,
        }
        race, created = Race.objects.get_or_create(**race_lookup, defaults=defaults)
        return self._apply_match(race, source, external_id, Race.MatchConfidence.VERIFIED), created

    def _select_match(self, queryset):
        matches = list(
            queryset.annotate(
                source_rank=Case(
                    *[When(source=source, then=index) for index, source in enumerate(SOURCE_PRIORITY)],
                    default=len(SOURCE_PRIORITY),
                    output_field=IntegerField(),
                )
            ).order_by('source_rank', 'id')[:2]
        )
        if not matches:
            return None
        if len(matches) > 1 and matches[0].source_rank == matches[1].source_rank:
            raise AmbiguousMatchError('Multiple races match at the same confidence tier.')
        return matches[0]

    def _apply_match(self, race: Race, source: str, external_id: str, confidence: str) -> Race:
        updates = []
        if race.match_confidence != confidence:
            race.match_confidence = confidence
            updates.append('match_confidence')
        if confidence in {Race.MatchConfidence.LOW, Race.MatchConfidence.FLAGGED} and race.race_status != Race.RaceStatus.PENDING_REVIEW:
            race.race_status = Race.RaceStatus.PENDING_REVIEW
            updates.append('race_status')
        if source in ENRICHMENT_SOURCES:
            source_metadata = dict(race.source_metadata or {})
            source_block = dict(source_metadata.get(source) or {})
            source_block['external_id'] = str(external_id)
            source_metadata[source] = source_block
            if source_metadata != (race.source_metadata or {}):
                race.source_metadata = source_metadata
                updates.append('source_metadata')
        if updates:
            race.save(update_fields=updates)
        return race

    def _resolve_election(self, source: str, external_id: str, payload: dict, election_date: date) -> Election:
        election_id = payload.get('election_id')
        if election_id:
            return Election.objects.get(pk=election_id)

        source_id = f'{source}:{external_id}'
        state = (payload.get('state') or '').upper() or None
        geography_scope = (payload.get('geography_scope') or '').lower()
        if not state:
            jurisdiction_level = Election.JurisdictionLevel.NATIONAL
        elif geography_scope in {'state', 'statewide'}:
            jurisdiction_level = Election.JurisdictionLevel.STATE
        else:
            jurisdiction_level = Election.JurisdictionLevel.LOCAL

        election, _ = Election.objects.get_or_create(
            source_id=source_id,
            defaults={
                'name': payload.get('election_name') or f'{state or "National"} Election {election_date.isoformat()}',
                'election_date': election_date,
                'jurisdiction_level': jurisdiction_level,
                'state': state,
                'status': self._infer_election_status(election_date),
            },
        )
        return election

    def _resolve_district_candidates(self, state: str, payload: dict, district_records: list, election_year: int):
        ocd_ids = set()
        names = set()

        for key in ('district', 'district_name', 'jurisdiction'):
            value = payload.get(key)
            if value:
                names.add(str(value).strip())
        district_number = payload.get('district_number')
        if district_number:
            names.add(str(district_number).strip())

        for record in district_records:
            if isinstance(record, DistrictRecord):
                if record.ocd_division_id:
                    ocd_ids.add(record.ocd_division_id)
                if record.name:
                    names.add(record.name)
                if record.district_number:
                    names.add(record.district_number)
                continue
            if not isinstance(record, dict):
                continue
            if record.get('ocd_division_id'):
                ocd_ids.add(record['ocd_division_id'])
            if record.get('name'):
                names.add(str(record['name']).strip())
            if record.get('district_number'):
                names.add(str(record['district_number']).strip())

        if not state or not names:
            return ocd_ids, names

        query = Q(state=state) & (Q(election_year_valid=election_year) | Q(election_year_valid__isnull=True))
        district_query = Q()
        for name in names:
            district_query |= Q(district_number__iexact=name) | Q(name__iexact=name)
        if district_query:
            ocd_ids.update(
                DistrictRecord.objects.filter(query & district_query).values_list('ocd_division_id', flat=True)
            )
        return ocd_ids, names

    @staticmethod
    def _coerce_date(value) -> date:
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))

    @staticmethod
    def _normalize(value: str) -> str:
        return ' '.join((value or '').strip().lower().split())

    @staticmethod
    def _infer_election_status(election_date: date) -> str:
        today = date.today()
        if election_date > today:
            return Election.Status.UPCOMING
        if election_date == today:
            return Election.Status.ACTIVE
        if election_date >= today - timedelta(days=30):
            return Election.Status.RESULTS_PENDING
        return Election.Status.ARCHIVED
