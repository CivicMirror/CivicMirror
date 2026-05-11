from rest_framework import serializers

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
    submitted_by_username = serializers.CharField(source='submitted_by.username', read_only=True)
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
            'submitted_by',
            'submitted_by_username',
            'race_status',
            'vote_method',
            'max_selections',
            'last_synced_at',
            'ocd_division_id',
            'normalized_office_title',
            'canonical_key',
            'candidates',
            'measure_options',
        )


class RaceSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Race
        fields = ('id', 'office_title', 'race_type', 'jurisdiction', 'geography_scope')
