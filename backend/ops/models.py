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

    class Meta:
        ordering = ['-started_at']

    def __str__(self) -> str:
        return f'{self.task_name or self.source} ({self.status})'
