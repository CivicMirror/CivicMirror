from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from elections.models import Candidate, Election, Race
from ops.models import SourceRecord

from .candidate_matcher import CandidateMatcher
from .enrichment import merge_source_metadata
from .exceptions import NoRaceFoundError
from .race_matcher import RaceMatcher
from .source_store import SourceRecordStore


class SourceRecordStoreTests(TestCase):
    def test_upsert_creates_and_detects_changes(self):
        store = SourceRecordStore()

        record, changed = store.upsert('fec', 'C001', {'name': 'Alice'})
        self.assertTrue(changed)
        self.assertEqual(SourceRecord.objects.count(), 1)
        self.assertEqual(record.external_id, 'C001')

        same_record, changed = store.upsert('fec', 'C001', {'name': 'Alice'})
        self.assertFalse(changed)
        self.assertEqual(record.pk, same_record.pk)

        updated_record, changed = store.upsert('fec', 'C001', {'name': 'Alice', 'party': 'Independent'})
        self.assertTrue(changed)
        updated_record.refresh_from_db()
        self.assertEqual(updated_record.raw_payload['party'], 'Independent')


class RaceMatcherTests(TestCase):
    def setUp(self):
        self.matcher = RaceMatcher()
        self.election_date = timezone.localdate() + timedelta(days=30)
        self.election = Election.objects.create(
            name='State General Election',
            election_date=self.election_date,
            jurisdiction_level=Election.JurisdictionLevel.STATE,
            state='NC',
            source_id='civic-2026-nc',
            status=Election.Status.UPCOMING,
        )

    def _payload(self, **overrides):
        payload = {
            'canonical_key': 'openelections:civic-2026-nc:governor:ocd-division/country:us/state:nc:candidate:2026-11-03',
            'ocd_division_id': 'ocd-division/country:us/state:nc',
            'normalized_office_title': 'governor',
            'office_title': 'Governor',
            'election_date': self.election_date,
            'state': 'NC',
            'race_type': Race.RaceType.CANDIDATE,
            'geography_scope': 'statewide',
            'jurisdiction': 'North Carolina',
        }
        payload.update(overrides)
        return payload

    def test_tier_one_matches_canonical_key(self):
        race = Race.objects.create(
            election=self.election,
            race_type=Race.RaceType.CANDIDATE,
            office_title='Governor',
            jurisdiction='North Carolina',
            geography_scope='statewide',
            source=Race.Source.OPENELECTIONS,
            vote_method=Race.VoteMethod.SINGLE_CHOICE,
            canonical_key='openelections:civic-2026-nc:governor:ocd-division/country:us/state:nc:candidate:2026-11-03',
            ocd_division_id='ocd-division/country:us/state:nc',
            normalized_office_title='governor',
        )

        matched_race, created = self.matcher.find_or_create('openelections', 'NC-GOV-2026', self._payload())

        self.assertFalse(created)
        self.assertEqual(matched_race.pk, race.pk)
        self.assertEqual(matched_race.match_confidence, Race.MatchConfidence.VERIFIED)

    def test_tier_two_matches_ocd_title_and_date(self):
        race = Race.objects.create(
            election=self.election,
            race_type=Race.RaceType.CANDIDATE,
            office_title='Governor',
            jurisdiction='North Carolina',
            geography_scope='statewide',
            source=Race.Source.CIVIC_API,
            vote_method=Race.VoteMethod.SINGLE_CHOICE,
            canonical_key='civic_api:civic-2026-nc:governor:ocd-division/country:us/state:nc:candidate:2026-11-03',
            ocd_division_id='ocd-division/country:us/state:nc',
            normalized_office_title='governor',
        )

        payload = self._payload(canonical_key='different-source-key')
        matched_race, created = self.matcher.find_or_create('openelections', 'NC-GOV-2026', payload)

        self.assertFalse(created)
        self.assertEqual(matched_race.pk, race.pk)
        self.assertEqual(matched_race.match_confidence, Race.MatchConfidence.HIGH)

    def test_tier_four_approximate_match_flags_pending_review(self):
        prior_election = Election.objects.create(
            name='Approximate Election',
            election_date=self.election_date + timedelta(days=10),
            jurisdiction_level=Election.JurisdictionLevel.STATE,
            state='NC',
            source_id='approx-election',
            status=Election.Status.UPCOMING,
        )
        race = Race.objects.create(
            election=prior_election,
            race_type=Race.RaceType.CANDIDATE,
            office_title='Governor',
            jurisdiction='North Carolina',
            geography_scope='statewide',
            source=Race.Source.CIVIC_API,
            vote_method=Race.VoteMethod.SINGLE_CHOICE,
            canonical_key='civic_api:approx-election:governor:ocd-division/country:us/state:nc:candidate:2026-11-13',
            ocd_division_id='',
            normalized_office_title='governor',
        )

        payload = self._payload(canonical_key='missing-key', ocd_division_id='')
        matched_race, created = self.matcher.find_or_create('openelections', 'NC-GOV-ALT', payload)
        matched_race.refresh_from_db()

        self.assertFalse(created)
        self.assertEqual(matched_race.pk, race.pk)
        self.assertEqual(matched_race.match_confidence, Race.MatchConfidence.LOW)
        self.assertEqual(matched_race.race_status, Race.RaceStatus.PENDING_REVIEW)

    def test_enrichment_source_without_match_raises(self):
        with self.assertRaises(NoRaceFoundError):
            self.matcher.find_or_create('fec', 'H0NC12001', self._payload(canonical_key='new-key', ocd_division_id=''))


class CandidateMatcherTests(TestCase):
    def setUp(self):
        self.matcher = CandidateMatcher()
        self.election = Election.objects.create(
            name='Candidate Election',
            election_date=timezone.localdate() + timedelta(days=30),
            jurisdiction_level=Election.JurisdictionLevel.STATE,
            state='NC',
            source_id='candidate-election',
            status=Election.Status.UPCOMING,
        )
        self.race = Race.objects.create(
            election=self.election,
            race_type=Race.RaceType.CANDIDATE,
            office_title='Governor',
            jurisdiction='North Carolina',
            geography_scope='statewide',
            source=Race.Source.CIVIC_API,
            vote_method=Race.VoteMethod.SINGLE_CHOICE,
            canonical_key='candidate-race',
            ocd_division_id='ocd-division/country:us/state:nc',
            normalized_office_title='governor',
        )
        self.candidate = Candidate.objects.create(
            race=self.race,
            name='Alex Smith',
            party='',
            source_metadata={},
        )

    def test_enrich_returns_enriched_when_party_updates(self):
        candidate, action = self.matcher.enrich(
            self.race,
            'fec',
            'H0NC12001',
            {'name': 'Alex Smith', 'party': 'Independent'},
        )

        self.assertEqual(action, 'enriched')
        self.assertEqual(candidate.pk, self.candidate.pk)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.party, 'Independent')
        self.assertEqual(self.candidate.source_metadata['fec']['external_id'], 'H0NC12001')

    def test_enrich_returns_skipped_when_no_fields_change(self):
        self.candidate.party = 'Independent'
        self.candidate.source_metadata = {
            'fec': {'external_id': 'H0NC12001'},
            '_field_sources': {'party': 'fec'},
        }
        self.candidate.save(update_fields=['party', 'source_metadata'])

        candidate, action = self.matcher.enrich(
            self.race,
            'fec',
            'H0NC12001',
            {'name': 'Alex Smith', 'party': 'Independent'},
        )

        self.assertEqual(action, 'skipped')
        self.assertEqual(candidate.pk, self.candidate.pk)

    def test_enrich_returns_no_match_when_candidate_missing(self):
        candidate, action = self.matcher.enrich(
            self.race,
            'fec',
            'H0NC12002',
            {'name': 'Jordan Lee', 'party': 'Independent'},
        )

        self.assertIsNone(candidate)
        self.assertEqual(action, 'no_match')

    def test_enrich_does_not_update_name(self):
        self.candidate.bioguide_id = 'BIO123'
        self.candidate.save(update_fields=['bioguide_id'])

        candidate, action = self.matcher.enrich(
            self.race,
            'congress',
            'BIO123',
            {
                'name': 'Alexandra Smith',
                'bioguide_id': 'BIO123',
                'website_url': 'https://example.com/alex',
            },
        )

        self.assertEqual(action, 'enriched')
        self.assertEqual(candidate.pk, self.candidate.pk)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.name, 'Alex Smith')
        self.assertEqual(self.candidate.website_url, 'https://example.com/alex')

    def test_enrich_without_race_matches_congressional_house_candidate(self):
        house_race = Race.objects.create(
            election=self.election,
            race_type=Race.RaceType.CANDIDATE,
            office_title='U.S. Representative District 05',
            jurisdiction='North Carolina District 05',
            geography_scope='district',
            source=Race.Source.CIVIC_API,
            vote_method=Race.VoteMethod.SINGLE_CHOICE,
            canonical_key='candidate-house-race',
            ocd_division_id='ocd-division/country:us/state:nc/cd:5',
            normalized_office_title='u.s. representative district 05',
        )
        house_candidate = Candidate.objects.create(
            race=house_race,
            name='Ada Lovelace',
            source_metadata={},
        )

        candidate, action = self.matcher.enrich(
            None,
            'congress',
            'BIO555',
            {
                'official_full_name': 'Ada Lovelace',
                'first_name': 'Ada',
                'last_name': 'Lovelace',
                'state': 'NC',
                'office_type': 'H',
                'district': '05',
                'bioguide_id': 'BIO555',
                'website_url': 'https://example.com/ada',
            },
        )

        self.assertEqual(action, 'enriched')
        self.assertEqual(candidate.pk, house_candidate.pk)
        house_candidate.refresh_from_db()
        self.assertEqual(house_candidate.bioguide_id, 'BIO555')
        self.assertEqual(house_candidate.website_url, 'https://example.com/ada')

    def test_enrich_without_race_returns_no_match_for_non_congressional_office(self):
        senate_race = Race.objects.create(
            election=self.election,
            race_type=Race.RaceType.CANDIDATE,
            office_title='NC Senate District 05',
            jurisdiction='North Carolina Senate District 05',
            geography_scope='district',
            source=Race.Source.CIVIC_API,
            vote_method=Race.VoteMethod.SINGLE_CHOICE,
            canonical_key='candidate-state-senate-race',
            ocd_division_id='ocd-division/country:us/state:nc/sldu:5',
            normalized_office_title='nc senate district 05',
        )
        Candidate.objects.create(
            race=senate_race,
            name='Ada Lovelace',
            source_metadata={},
        )

        candidate, action = self.matcher.enrich(
            None,
            'congress',
            'BIO999',
            {
                'official_full_name': 'Ada Lovelace',
                'state': 'NC',
                'office_type': 'S',
                'district': '',
                'bioguide_id': 'BIO999',
                'website_url': 'https://example.com/ada',
            },
        )

        self.assertIsNone(candidate)
        self.assertEqual(action, 'no_match')


class MergeSourceMetadataTests(TestCase):
    def test_merge_source_metadata_preserves_other_sources(self):
        existing = {
            'civic_api': {'external_id': 'existing'},
            '_field_sources': {'party': 'civic_api'},
        }

        merged = merge_source_metadata(existing, 'fec', {'external_id': 'new-id'})

        self.assertEqual(merged['civic_api']['external_id'], 'existing')
        self.assertEqual(merged['fec']['external_id'], 'new-id')
        self.assertEqual(merged['_field_sources']['party'], 'civic_api')
