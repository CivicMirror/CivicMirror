from celery import shared_task
from django.utils import timezone
from knox.models import AuthToken


@shared_task
def cleanup_expired_tokens():
    deleted_count, _ = AuthToken.objects.filter(expiry__lt=timezone.now()).delete()
    return deleted_count
