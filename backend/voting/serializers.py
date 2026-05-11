from django.db import transaction
from rest_framework import serializers

from elections.models import Candidate, MeasureOption, Race

from .models import MockVote


class MockVoteSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.name', read_only=True)
    measure_option_label = serializers.CharField(source='measure_option.option_label', read_only=True)
    race_title = serializers.CharField(source='race.office_title', read_only=True)
    race = serializers.PrimaryKeyRelatedField(queryset=Race.objects.all())
    candidate = serializers.PrimaryKeyRelatedField(queryset=Candidate.objects.all(), allow_null=True, required=False)
    measure_option = serializers.PrimaryKeyRelatedField(queryset=MeasureOption.objects.all(), allow_null=True, required=False)

    class Meta:
        model = MockVote
        fields = (
            'id',
            'race',
            'race_title',
            'candidate',
            'candidate_name',
            'measure_option',
            'measure_option_label',
            'cast_at',
        )
        read_only_fields = ('id', 'cast_at')

    def validate(self, attrs):
        race = attrs['race']
        candidate = attrs.get('candidate')
        measure_option = attrs.get('measure_option')

        if bool(candidate) == bool(measure_option):
            raise serializers.ValidationError('Provide exactly one of candidate or measure_option.')
        if candidate and candidate.race_id != race.id:
            raise serializers.ValidationError({'candidate': ['Selected candidate does not belong to the selected race.']})
        if measure_option and measure_option.race_id != race.id:
            raise serializers.ValidationError({'measure_option': ['Selected measure option does not belong to the selected race.']})
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        with transaction.atomic():
            return MockVote.objects.create(user=user, **validated_data)
