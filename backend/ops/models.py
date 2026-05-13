from django.db import models


class SyncLog(models.Model):
    class Status(models.TextChoices):
        STARTED = 'started', 'Started'
        COMPLETED = 'completed', 'Completed'
        COMPLETED_WITH_WARNINGS = 'completed_with_warnings', 'Completed with Warnings'
        FAILED = 'failed', 'Failed'

    election = models.ForeignKey('elections.Election', null=True, blank=True, on_delete=models.SET_NULL, related_name='sync_logs')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    records_created = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)
    source = models.CharField(max_length=50, blank=True)
    task_name = models.CharField(max_length=100, blank=True)
    address_label = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=30, default=Status.STARTED, choices=Status.choices)
    cycle_year = models.IntegerField(null=True, blank=True)
    records_skipped = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self) -> str:
        return f'{self.task_name or self.source} ({self.status})'


class SourceRecord(models.Model):
    class SourceType(models.TextChoices):
        CIVIC = 'civic', 'Google Civic'
        FEC = 'fec', 'OpenFEC'
        CONGRESS = 'congress', 'Congress Legislators'
        OPENSTATES = 'openstates', 'Open States'
        CENSUS = 'census', 'U.S. Census'
        OPENELECTIONS = 'openelections', 'OpenElections'
        MEDSL = 'medsl', 'MEDSL'

    source = models.CharField(max_length=30, choices=SourceType.choices)
    external_id = models.CharField(max_length=255)
    raw_payload = models.JSONField()
    payload_checksum = models.CharField(max_length=64)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    linked_race = models.ForeignKey(
        'elections.Race',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='source_records',
    )
    linked_candidate = models.ForeignKey(
        'elections.Candidate',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='source_records',
    )

    class Meta:
        unique_together = [('source', 'external_id')]
        indexes = [
            models.Index(fields=['source', 'external_id']),
            models.Index(fields=['linked_race']),
        ]

    def __str__(self):
        return f'{self.source}:{self.external_id}'
