import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

app = Celery('civicmirror')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.beat_schedule = {
    'sync-elections-hourly': {
        'task': 'integrations.civic.tasks.sync_elections',
        'schedule': crontab(minute=0),
    },
    'cleanup-expired-knox-tokens-daily': {
        'task': 'accounts.tasks.cleanup_expired_tokens',
        'schedule': crontab(minute=0, hour=0),
    },
    'auto-close-community-races-daily': {
        'task': 'elections.tasks.auto_close_community_races',
        'schedule': crontab(minute=0, hour=1),
    },
}
