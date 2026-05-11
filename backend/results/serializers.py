from rest_framework import serializers

from .models import OfficialResult


class OfficialResultSerializer(serializers.ModelSerializer):
    candidate_name = serializers.SerializerMethodField()
    option_label = serializers.SerializerMethodField()
    vote_pct = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True, coerce_to_string=False)

    def get_candidate_name(self, obj):
        if obj.is_write_in_aggregate:
            return 'Write-in (aggregate)'
        return obj.candidate.name if obj.candidate else None

    def get_option_label(self, obj):
        return obj.measure_option.option_label if obj.measure_option else None

    class Meta:
        model = OfficialResult
        fields = [
            'id',
            'candidate_name',
            'option_label',
            'vote_count',
            'vote_pct',
            'is_winner',
            'result_type',
            'certified_at',
            'source_url',
            'round_number',
            'is_write_in_aggregate',
            'jurisdiction_fragment',
        ]
