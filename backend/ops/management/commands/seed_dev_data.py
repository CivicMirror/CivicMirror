from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import UserProfile
from elections.models import Candidate, Election, MeasureOption, Race
from legal.models import TermsAcceptance, TermsOfUseVersion
from voting.models import MockVote

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed deterministic development data for CivicMirror.'

    def handle(self, *args, **options):
        if Election.objects.filter(source_id__startswith='seed-').exists():
            self.stdout.write(self.style.WARNING('Seed data already exists; skipping.'))
            return

        now = timezone.now()
        active_terms, _ = TermsOfUseVersion.objects.update_or_create(
            version='2025-01',
            defaults={
                'content_checksum': 'dev-seed-checksum-2025-01',
                'published_at': now,
                'is_active': True,
            },
        )
        TermsOfUseVersion.objects.exclude(pk=active_terms.pk).update(is_active=False)

        elections = [
            Election.objects.create(
                name='2026 CivicMirror National General Election',
                election_date=(now + timedelta(days=45)).date(),
                jurisdiction_level=Election.JurisdictionLevel.NATIONAL,
                state=None,
                source_id='seed-upcoming-2026',
                status=Election.Status.UPCOMING,
            ),
            Election.objects.create(
                name='2025 Massachusetts Primary',
                election_date=now.date(),
                jurisdiction_level=Election.JurisdictionLevel.STATE,
                state='MA',
                source_id='seed-active-2025',
                status=Election.Status.ACTIVE,
            ),
        ]

        candidate_races = []
        for election, title, jurisdiction, scope in [
            (elections[0], 'President of the United States', 'United States', 'federal'),
            (elections[0], 'U.S. Senate', 'Massachusetts', 'statewide'),
            (elections[0], 'Governor', 'Massachusetts', 'statewide'),
            (elections[1], 'Attorney General', 'Massachusetts', 'statewide'),
            (elections[1], 'Mayor', 'Boston', 'city'),
        ]:
            candidate_races.append(
                Race.objects.create(
                    election=election,
                    race_type=Race.RaceType.CANDIDATE,
                    office_title=title,
                    jurisdiction=jurisdiction,
                    geography_scope=scope,
                    certification_status=Race.CertificationStatus.UPCOMING,
                    source=Race.Source.COMMUNITY,
                    race_status=Race.RaceStatus.ACTIVE,
                    vote_method=Race.VoteMethod.SINGLE_CHOICE,
                    max_selections=1,
                    normalized_office_title=' '.join(title.lower().split()),
                    canonical_key=f'seed:{election.source_id}:{title.lower().replace(" ", "_")}',
                )
            )

        measure_races = []
        for election, title, jurisdiction in [
            (elections[0], 'Question 1: Clean Water Bond', 'Massachusetts'),
            (elections[1], 'Question 2: Library Funding Override', 'Boston'),
        ]:
            measure_races.append(
                Race.objects.create(
                    election=election,
                    race_type=Race.RaceType.MEASURE,
                    office_title=title,
                    jurisdiction=jurisdiction,
                    geography_scope='statewide' if jurisdiction == 'Massachusetts' else 'city',
                    certification_status=Race.CertificationStatus.UPCOMING,
                    source=Race.Source.COMMUNITY,
                    race_status=Race.RaceStatus.ACTIVE,
                    vote_method=Race.VoteMethod.YES_NO,
                    max_selections=1,
                    normalized_office_title=' '.join(title.lower().split()),
                    canonical_key=f'seed:{election.source_id}:{title.lower().replace(" ", "_")}',
                )
            )

        candidate_names = [
            ['Alex Rivera', 'Jordan Kim', 'Taylor Brooks'],
            ['Morgan Lee', 'Jamie Carter'],
            ['Cameron Diaz', 'Riley Chen', 'Avery Singh'],
            ['Robin Flores', 'Casey Patel'],
            ['Sydney Lopez', 'Dakota Nguyen', 'Quinn Adams', 'Harper Reed'],
        ]
        for race, names in zip(candidate_races, candidate_names, strict=True):
            for index, name in enumerate(names):
                Candidate.objects.create(
                    race=race,
                    name=name,
                    party=['Independent', 'Democratic', 'Republican', 'Green'][index % 4],
                    incumbent=index == 0,
                )

        for race in measure_races:
            for option_label in ['Yes', 'No', 'Abstain']:
                MeasureOption.objects.create(race=race, option_label=option_label)

        profiles = []
        user_specs = [
            ('seed_voter_1', 'password123!Aa', '18-24', 'US', 'MA', 'female'),
            ('seed_voter_2', 'password123!Bb', '25-34', 'US', 'CA', 'male'),
            ('seed_voter_3', 'password123!Cc', '35-44', 'US', 'TX', 'nonbinary'),
        ]
        for username, password, age_range, country, us_state, gender in user_specs:
            user = User.objects.create_user(username=username, password=password)
            profile = UserProfile.objects.create(
                user=user,
                username=username,
                age_range=age_range,
                country=country,
                us_state=us_state,
                gender=gender,
            )
            TermsAcceptance.objects.get_or_create(user=user, terms_version=active_terms, defaults={'ip_hash': ''})
            profiles.append(profile)

        all_races = candidate_races + measure_races

        created_votes = 0
        for race_index, race in enumerate(all_races):
            targets = list(race.candidates.all()) or list(race.measure_options.all())
            if not targets:
                continue
            for profile_index, profile in enumerate(profiles):
                if created_votes >= 20:
                    break
                target = targets[(race_index + profile_index) % len(targets)]
                if isinstance(target, Candidate):
                    MockVote.objects.create(user=profile.user, race=race, candidate=target)
                else:
                    MockVote.objects.create(user=profile.user, race=race, measure_option=target)
                created_votes += 1
            if created_votes >= 20:
                break

        self.stdout.write(self.style.SUCCESS('Seed data created successfully.'))
