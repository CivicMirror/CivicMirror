from django.utils import timezone
from rest_framework import serializers

from voting.models import MockVote
from voting.services import build_choice_payload_from_vote, build_tally_payload

from .models import Candidate, Election, MeasureOption, Race


class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = (
            'id',
            'race',
            'name',
            'party',
            'incumbent',
            'candidate_status',
            'description',
            'image_url',
            'website_url',
        )


class MeasureOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasureOption
        fields = ('id', 'race', 'option_label')


class ElectionSerializer(serializers.ModelSerializer):
    race_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Election
        fields = (
            'id',
            'name',
            'election_date',
            'jurisdiction_level',
            'state',
            'source_id',
            'status',
            'last_synced_at',
            'race_count',
        )


class RaceSerializer(serializers.ModelSerializer):
    election_name = serializers.CharField(source='election.name', read_only=True)
    election_date = serializers.DateField(source='election.election_date', read_only=True)
    state = serializers.CharField(source='election.state', read_only=True)
    submitter_username = serializers.CharField(source='submitter.username', read_only=True)
    candidates = CandidateSerializer(many=True, read_only=True)
    measure_options = MeasureOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Race
        fields = (
            'id',
            'election',
            'election_name',
            'election_date',
            'state',
            'race_type',
            'office_title',
            'jurisdiction',
            'geography_scope',
            'voting_opens',
            'voting_closes',
            'certification_status',
            'source',
            'community_status',
            'submitter',
            'submitter_username',
            'submitted_at',
            'source_links',
            'location_name',
            'race_status',
            'vote_method',
            'max_selections',
            'last_synced_at',
            'ocd_division_id',
            'normalized_office_title',
            'canonical_key',
            'ballot_type',
            'yes_vote_details',
            'no_vote_details',
            'supporting_links',
            'candidates',
            'measure_options',
        )


class RaceDetailSerializer(RaceSerializer):
    tally_summary = serializers.SerializerMethodField()
    viewer_has_voted = serializers.SerializerMethodField()
    viewer_choice = serializers.SerializerMethodField()

    class Meta(RaceSerializer.Meta):
        fields = RaceSerializer.Meta.fields + ('tally_summary', 'viewer_has_voted', 'viewer_choice')

    def get_tally_summary(self, obj):
        summary = build_tally_payload(obj, include_percent=False, include_breakdowns=False)
        return {'total_votes': summary['total_votes'], 'options': summary['options']}

    def _get_viewer_vote(self, obj):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return None

        cache = self.context.setdefault('_viewer_vote_cache', {})
        if obj.id not in cache:
            cache[obj.id] = MockVote.objects.select_related('candidate', 'measure_option').filter(user=request.user, race=obj).first()
        return cache[obj.id]

    def get_viewer_has_voted(self, obj):
        return self._get_viewer_vote(obj) is not None

    def get_viewer_choice(self, obj):
        vote = self._get_viewer_vote(obj)
        if vote is None:
            return None
        return build_choice_payload_from_vote(vote)


class RaceSummarySerializer(serializers.ModelSerializer):
    election_date = serializers.DateField(source='election.election_date', read_only=True)

    class Meta:
        model = Race
        fields = ('id', 'office_title', 'race_type', 'jurisdiction', 'geography_scope', 'election_date', 'location_name')


class CommunityCandidateSubmissionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    party = serializers.CharField(max_length=100, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    image_url = serializers.URLField(required=False, allow_blank=True)
    website_url = serializers.URLField(required=False, allow_blank=True)
    candidate_type = serializers.ChoiceField(
        choices=[Candidate.CandidateStatus.RUNNING, Candidate.CandidateStatus.WRITE_IN],
        required=False,
        default=Candidate.CandidateStatus.RUNNING,
    )


class CommunityRaceSubmissionSerializer(serializers.Serializer):
    race_type = serializers.ChoiceField(choices=Race.RaceType.values)
    office_title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    question_title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    jurisdiction = serializers.CharField(max_length=255, required=False, allow_blank=True)
    election_date = serializers.DateField()
    location_name = serializers.CharField(max_length=255)
    source_links = serializers.ListField(child=serializers.URLField(), required=False, default=list)
    supporting_links = serializers.ListField(child=serializers.URLField(), required=False, default=list)
    candidates = CommunityCandidateSubmissionSerializer(many=True, required=False)
    ballot_type = serializers.CharField(max_length=100, required=False, allow_blank=True)
    yes_vote_details = serializers.CharField(required=False, allow_blank=True)
    no_vote_details = serializers.CharField(required=False, allow_blank=True)
    force_submit = serializers.BooleanField(required=False, default=False)

    def validate_election_date(self, value):
        if value <= timezone.localdate():
            raise serializers.ValidationError('Election date must be in the future.')
        return value

    def validate(self, attrs):
        race_type = attrs['race_type']
        errors = {}

        if race_type == Race.RaceType.CANDIDATE:
            office_title = attrs.get('office_title', '').strip()
            jurisdiction = attrs.get('jurisdiction', '').strip()
            candidates = attrs.get('candidates') or []
            if not office_title:
                errors['office_title'] = ['This field is required for candidate races.']
            if not jurisdiction:
                errors['jurisdiction'] = ['This field is required for candidate races.']
            if not candidates:
                errors['candidates'] = ['Provide at least one candidate.']
            elif len(candidates) > 10:
                errors['candidates'] = ['No more than 10 candidates may be submitted.']
            else:
                candidate_names = [candidate['name'].strip().lower() for candidate in candidates]
                if len(candidate_names) != len(set(candidate_names)):
                    errors['candidates'] = ['Candidate names must be unique within a submission.']
        else:
            question_title = attrs.get('question_title', '').strip()
            ballot_type = attrs.get('ballot_type', '').strip()
            if not question_title:
                errors['question_title'] = ['This field is required for measure races.']
            if not ballot_type:
                errors['ballot_type'] = ['This field is required for measure races.']
            if not attrs.get('yes_vote_details', '').strip() and not attrs.get('no_vote_details', '').strip():
                errors['non_field_errors'] = ['Provide yes_vote_details or no_vote_details for measure races.']

        if errors:
            raise serializers.ValidationError(errors)
        return attrs
