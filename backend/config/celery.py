import logging
import os
from importlib import import_module

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

logger = logging.getLogger(__name__)

OPENELECTIONS_STATES = [
    'al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'de', 'fl', 'ga', 'hi', 'id', 'il', 'in', 'ia',
    'ks', 'ky', 'la', 'me', 'md', 'ma', 'mi', 'mn', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh', 'nj',
    'nm', 'ny', 'nc', 'nd', 'oh', 'ok', 'or', 'pa', 'ri', 'sc', 'sd', 'tn', 'tx', 'ut', 'vt',
    'va', 'wa', 'wv', 'wi', 'wy',
]


app = Celery('civicmirror')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


# TODO: Move this wrapper into integrations/openelections/tasks.py once the OpenElections adapter lands.
@app.task(name='integrations.openelections.tasks.check_openelections_all_states')
def check_openelections_all_states():
    try:
        task_module = import_module('integrations.openelections.tasks')
    except ModuleNotFoundError as exc:
        if exc.name not in {'integrations.openelections', 'integrations.openelections.tasks'}:
            raise
        logger.warning('OpenElections tasks are not yet implemented; skipping scheduled fan-out.')
        return {'queued': 0, 'status': 'not_implemented'}

    state_task = getattr(task_module, 'check_openelections_new_results', None)
    if state_task is None:
        logger.warning('OpenElections state sync task is missing; skipping scheduled fan-out.')
        return {'queued': 0, 'status': 'not_implemented'}

    for i, state in enumerate(OPENELECTIONS_STATES):
        state_task.apply_async(kwargs={'state': state}, countdown=i * 10)

    return {'queued': len(OPENELECTIONS_STATES), 'spacing_seconds': 10}


app.conf.beat_schedule = {
    # NOTE: sync-elections-hourly removed — election data is now served by the
    # dedicated CivicMirror-API (civicmirror-worker). The integrations.civic
    # module is retained for reference but is no longer scheduled.
    'cleanup-expired-knox-tokens-daily': {
        'task': 'accounts.tasks.cleanup_expired_tokens',
        'schedule': crontab(minute=0, hour=0),
    },
    'auto-close-community-races-daily': {
        'task': 'elections.tasks.auto_close_community_races',
        'schedule': crontab(minute=0, hour=1),
    },
    'sync-fec-candidates-nightly': {
        'task': 'integrations.fec.tasks.sync_fec_candidates',
        'schedule': crontab(minute=0, hour=2),
    },
    'sync-congress-legislators-weekly': {
        'task': 'integrations.congress.tasks.sync_congress_legislators',
        'schedule': crontab(minute=0, hour=3, day_of_week='sunday'),
    },
    'sync-openstates-all-states-nightly': {
        'task': 'integrations.openstates.tasks.sync_openstates_all_states',
        'schedule': crontab(minute=0, hour=4),
    },
    'refresh-district-records-monthly': {
        'task': 'integrations.census.tasks.refresh_district_records',
        'schedule': crontab(minute=0, hour=5, day_of_month=1),
    },
    'check-openelections-all-states-weekly': {
        'task': 'integrations.openelections.tasks.check_openelections_all_states',
        'schedule': crontab(minute=0, hour=0, day_of_week='saturday'),
    },
}
