from rest_framework import serializers

from .models import OfficialResult


class OfficialResultSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.name', read_only=True)
    measure_option_label = serializers.CharField(source='measure_option.option_label', read_only=True)
    race_title = serializers.CharField(source='race.office_title', read_only=True)

    class Meta:
        model = OfficialResult
        fields = (
            'id',
            'race',
            'race_title',
            'candidate',
            'candidate_name',
            'measure_option',
            'measure_option_label',
            'vote_count',
            'vote_pct',
            'certified_at',
            'source_url',
            'result_type',
            'is_winner',
            'raw_payload',
        )
