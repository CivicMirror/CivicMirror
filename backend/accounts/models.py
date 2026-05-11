from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    age_range = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2, blank=True)
    us_state = models.CharField(max_length=2, blank=True)
    gender = models.CharField(max_length=30, blank=True)
    username = models.CharField(max_length=50, unique=True)
    saved_zipcode = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['username'])]
        ordering = ['username']

    def __str__(self) -> str:
        return self.username
