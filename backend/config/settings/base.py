from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parents[2]

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    CIVIC_HTTP_TIMEOUT_SECONDS=(int, 10),
    CIVIC_MAX_RETRIES=(int, 3),
    CIVIC_RETRY_BACKOFF_SECONDS=(float, 1.0),
)
environ.Env.read_env(BASE_DIR / '.env')


def _csv_env(name: str, default: list[str] | None = None) -> list[str]:
    value = env(name, default='')
    if isinstance(value, list):
        return value
    if not value:
        return default or []
    return [item.strip() for item in str(value).split(',') if item.strip()]


SECRET_KEY = env('DJANGO_SECRET_KEY', default='django-insecure-change-me')
DEBUG = env.bool('DJANGO_DEBUG', default=False)
ALLOWED_HOSTS = _csv_env('DJANGO_ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
FRONTEND_BASE_URL = env('FRONTEND_BASE_URL', default='http://localhost:5173')
CORS_ALLOWED_ORIGINS = _csv_env('CORS_ALLOWED_ORIGINS', default=[FRONTEND_BASE_URL])
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'knox',
    'drf_spectacular',
    'django_filters',
    'accounts',
    'elections',
    'voting',
    'results',
    'ops',
    'legal',
    'integrations.civic',
    'integrations.census',
    'integrations.congress',
    'integrations.fec',
    'integrations.openstates',
    'integrations.openelections',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

DATABASES = {
    'default': env.db('DATABASE_URL', default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}
DATABASES['default']['ATOMIC_REQUESTS'] = False
DATABASES['default']['CONN_MAX_AGE'] = env.int('DJANGO_CONN_MAX_AGE', default=0)

REDIS_URL = env('REDIS_URL', default='')
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'civicmirror-local',
        }
    }

CELERY_BROKER_URL = env('CELERY_BROKER_URL', default=REDIS_URL or 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default=REDIS_URL or 'redis://127.0.0.1:6379/1')
CELERY_TASK_ALWAYS_EAGER = env.bool('CELERY_TASK_ALWAYS_EAGER', default=False)
CELERY_TASK_EAGER_PROPAGATES = env.bool('CELERY_TASK_EAGER_PROPAGATES', default=False)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['knox.auth.TokenAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser'],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '300/hour',
        'user': '2000/hour',
        'register': '10/hour',
        'login': '30/hour',
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'api.exceptions.custom_exception_handler',
}

REST_KNOX = {
    'TOKEN_TTL': timedelta(days=30),
    'AUTO_REFRESH': False,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'CivicMirror API',
    'DESCRIPTION': 'Mock civic voting and election comparison backend for CivicMirror.',
    'VERSION': '1.0.0',
}

CIVIC_API_KEY = env('CIVIC_API_KEY', default='')
FEC_API_KEY = env('FEC_API_KEY', default='')
OPENSTATES_API_KEY = env('OPENSTATES_API_KEY', default='')
GITHUB_TOKEN = env('GITHUB_TOKEN', default='')
CIVIC_API_BASE = env('CIVIC_API_BASE', default='https://www.googleapis.com/civicinfo/v2')
CIVIC_HTTP_TIMEOUT_SECONDS = env.int('CIVIC_HTTP_TIMEOUT_SECONDS', default=10)
CIVIC_MAX_RETRIES = env.int('CIVIC_MAX_RETRIES', default=3)
CIVIC_RETRY_BACKOFF_SECONDS = env.float('CIVIC_RETRY_BACKOFF_SECONDS', default=1.0)
