from .base import *  # noqa: F401,F403

DEBUG = env.bool('DJANGO_DEBUG', default=True)
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['*']
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Human-readable logs in development instead of JSON
LOGGING['handlers']['console']['formatter'] = 'verbose'
