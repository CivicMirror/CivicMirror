from rest_framework import serializers

from .models import MockVote
from .services import build_choice_payload_from_vote


class VoteCastRequestSerializer(serializers.Serializer):
    candidate_id = serializers.IntegerField(required=False)
    measure_option_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        if bool(attrs.get('candidate_id')) == bool(attrs.get('measure_option_id')):
            raise serializers.ValidationError('Provide exactly one of candidate_id or measure_option_id.')
        return attrs


class MockVoteResponseSerializer(serializers.ModelSerializer):
    race_id = serializers.IntegerField(source='race.id', read_only=True)
    candidate_id = serializers.IntegerField(source='candidate.id', read_only=True, allow_null=True)
    measure_option_id = serializers.IntegerField(source='measure_option.id', read_only=True, allow_null=True)

    class Meta:
        model = MockVote
        fields = ('id', 'race_id', 'cast_at', 'candidate_id', 'measure_option_id')


class VoteHistorySerializer(serializers.ModelSerializer):
    race_id = serializers.IntegerField(source='race.id', read_only=True)
    election_name = serializers.CharField(source='race.election.name', read_only=True)
    office_title = serializers.CharField(source='race.office_title', read_only=True)
    jurisdiction = serializers.CharField(source='race.jurisdiction', read_only=True)
    choice = serializers.SerializerMethodField()
    race_status = serializers.CharField(source='race.race_status', read_only=True)

    class Meta:
        model = MockVote
        fields = (
            'id',
            'race_id',
            'election_name',
            'office_title',
            'jurisdiction',
            'cast_at',
            'choice',
            'race_status',
        )

    def get_choice(self, obj):
        return build_choice_payload_from_vote(obj)
