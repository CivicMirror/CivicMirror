from __future__ import annotations

import logging
import time

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class OpenStatesError(Exception):
    pass


class OpenStatesRateLimitError(OpenStatesError):
    pass


class OpenStatesForbiddenError(OpenStatesError):
    pass


class OpenStatesClient:
    BASE_URL = 'https://v3.openstates.org'

    def __init__(self):
        self.api_key = settings.OPENSTATES_API_KEY
        self.base_url = self.BASE_URL.rstrip('/')
        self.timeout = getattr(settings, 'CIVIC_HTTP_TIMEOUT_SECONDS', 10)
        self.max_retries = getattr(settings, 'CIVIC_MAX_RETRIES', 3)
        self.backoff_seconds = getattr(settings, 'CIVIC_RETRY_BACKOFF_SECONDS', 1.0)
        self.session = requests.Session()

    def list_people(
        self,
        state: str,
        page: int = 1,
        per_page: int = 50,
    ) -> dict:
        if not self.api_key:
            raise OpenStatesForbiddenError('OPENSTATES_API_KEY is not configured.')

        jurisdiction = f"ocd-division/country:us/state:{(state or '').lower()}"
        params = {
            'jurisdiction': jurisdiction,
            'page': page,
            'per_page': per_page,
            'apikey': self.api_key,
            'api_key': self.api_key,
        }
        url = f'{self.base_url}/people'

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
            except requests.RequestException as exc:
                if attempt >= self.max_retries:
                    raise OpenStatesError('Unable to reach the Open States API.') from exc
                time.sleep(self.backoff_seconds * (2 ** attempt))
                continue

            if response.status_code == 403:
                raise OpenStatesForbiddenError('Open States rejected the configured API key.')
            if response.status_code == 429:
                raise OpenStatesRateLimitError('Open States rate limit exceeded.')

            if response.status_code == 503 or 500 <= response.status_code < 600:
                logger.warning(
                    'Retrying Open States people request state=%s status=%s attempt=%s',
                    state,
                    response.status_code,
                    attempt + 1,
                )
                if attempt >= self.max_retries:
                    raise OpenStatesError(f'Open States returned retryable status {response.status_code}.')
                time.sleep(self.backoff_seconds * (2 ** attempt))
                continue

            try:
                response.raise_for_status()
                return response.json()
            except (requests.RequestException, ValueError) as exc:
                if attempt >= self.max_retries:
                    raise OpenStatesError('Open States request failed.') from exc
                time.sleep(self.backoff_seconds * (2 ** attempt))

        raise OpenStatesError('Open States request retries were exhausted.')

    def list_people_all_pages(self, state: str) -> list[dict]:
        people: list[dict] = []
        page = 1
        per_page = 50

        while True:
            payload = self.list_people(state=state, page=page, per_page=per_page)
            results = payload.get('results') or []
            people.extend(results)

            pagination = payload.get('pagination') or {}
            max_page = pagination.get('max_page') or pagination.get('pages')
            if max_page:
                if page >= int(max_page):
                    break
            else:
                if not results or len(results) < per_page:
                    break
            page += 1

        return people
