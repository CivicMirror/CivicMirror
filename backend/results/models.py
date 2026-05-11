from django.db import models
from django.db.models import Q


class OfficialResult(models.Model):
    class ResultType(models.TextChoices):
        OFFICIAL = 'official', 'Official'
        UNOFFICIAL = 'unofficial', 'Unofficial'

    race = models.ForeignKey('elections.Race', on_delete=models.CASCADE, related_name='official_results')
    candidate = models.ForeignKey('elections.Candidate', null=True, blank=True, on_delete=models.SET_NULL, related_name='official_results')
    measure_option = models.ForeignKey('elections.MeasureOption', null=True, blank=True, on_delete=models.SET_NULL, related_name='official_results')
    vote_count = models.BigIntegerField(default=0)
    vote_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    certified_at = models.DateTimeField(null=True, blank=True)
    source_url = models.URLField(blank=True)
    result_type = models.CharField(max_length=20, default=ResultType.UNOFFICIAL, choices=ResultType.choices)
    is_winner = models.BooleanField(null=True, blank=True)
    round_number = models.PositiveSmallIntegerField(null=True, blank=True)
    jurisdiction_fragment = models.CharField(max_length=255, blank=True)
    is_write_in_aggregate = models.BooleanField(default=False)
    raw_payload = models.JSONField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['race', 'round_number'])]
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(is_write_in_aggregate=True)
                    | (Q(candidate__isnull=False) & Q(measure_option__isnull=True))
                    | (Q(candidate__isnull=True) & Q(measure_option__isnull=False))
                ),
                name='result_target_valid',
            )
        ]
        ordering = ['round_number', '-vote_count', 'id']

    def __str__(self) -> str:
        return f'{self.race.office_title} - {self.vote_count}'
