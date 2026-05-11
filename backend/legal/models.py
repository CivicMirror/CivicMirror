from django.conf import settings
from django.db import models


class TermsOfUseVersion(models.Model):
    version = models.CharField(max_length=20, unique=True)
    content_checksum = models.CharField(max_length=64)
    published_at = models.DateTimeField()
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ['-published_at']

    def __str__(self) -> str:
        return self.version


class TermsAcceptance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='terms_acceptances')
    terms_version = models.ForeignKey(TermsOfUseVersion, on_delete=models.PROTECT, related_name='acceptances')
    accepted_at = models.DateTimeField(auto_now_add=True)
    ip_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'terms_version'], name='unique_terms_acceptance_per_user_version')
        ]
        ordering = ['-accepted_at']

    def __str__(self) -> str:
        return f'{self.user_id}:{self.terms_version.version}'
