FROM python:3.12-slim AS base

# Install system deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements/base.txt requirements/base.txt
RUN pip install --no-cache-dir -r requirements/base.txt

# Copy source
COPY . .

# Collect static files (needed for Django admin + WhiteNoise)
# SECRET_KEY is only used at import time; a dummy value is safe for collectstatic.
RUN SECRET_KEY=build-only DJANGO_SETTINGS_MODULE=config.settings.base \
    python manage.py collectstatic --noinput

# Run as non-root
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers ${GUNICORN_WORKERS:-2} --timeout ${GUNICORN_TIMEOUT:-120} --access-logfile - --error-logfile -"]
