from django.conf import settings
from django.db import models
from django.db.models import Q


class MockVote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mock_votes')
    race = models.ForeignKey('elections.Race', on_delete=models.CASCADE, related_name='mock_votes')
    candidate = models.ForeignKey('elections.Candidate', null=True, blank=True, on_delete=models.SET_NULL, related_name='mock_votes')
    measure_option = models.ForeignKey('elections.MeasureOption', null=True, blank=True, on_delete=models.SET_NULL, related_name='mock_votes')
    cast_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(Q(candidate__isnull=False) & Q(measure_option__isnull=True))
                | (Q(candidate__isnull=True) & Q(measure_option__isnull=False)),
                name='exactly_one_vote_target',
            ),
            models.UniqueConstraint(fields=['user', 'race'], name='unique_user_race_vote'),
        ]
        indexes = [models.Index(fields=['race', 'cast_at'])]
        ordering = ['-cast_at']

    def __str__(self) -> str:
        return f'{self.user.username} -> {self.race.office_title}'
