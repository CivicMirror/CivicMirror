import logging
import time

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class FECAPIError(Exception):
    pass


class FECAPIForbidden(FECAPIError):
    pass


class FECAPIRateLimitError(FECAPIError):
    pass


class FECClient:
    BASE_URL = 'https://api.open.fec.gov/v1'
    MIN_REQUEST_INTERVAL = 4.0

    def __init__(self):
        self.api_key = settings.FEC_API_KEY
        self.base_url = getattr(settings, 'FEC_API_BASE', self.BASE_URL).rstrip('/')
        self.timeout = getattr(settings, 'FEC_HTTP_TIMEOUT_SECONDS', 10)
        self.max_retries = getattr(settings, 'FEC_MAX_RETRIES', 3)
        self.backoff_seconds = getattr(settings, 'FEC_RETRY_BACKOFF_SECONDS', 1.0)
        self.session = requests.Session()
        self._last_request_at: float | None = None

    def _throttle(self):
        if self._last_request_at is None:
            return

        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.MIN_REQUEST_INTERVAL:
            time.sleep(self.MIN_REQUEST_INTERVAL - elapsed)

    def _request(self, endpoint: str, params: dict) -> dict:
        if not self.api_key:
            raise FECAPIForbidden('FEC_API_KEY is not configured.')

        merged_params = {**params, 'api_key': self.api_key}
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(self.max_retries + 1):
            self._throttle()
            try:
                response = self.session.get(url, params=merged_params, timeout=self.timeout)
            except requests.RequestException as exc:
                self._last_request_at = time.monotonic()
                if attempt >= self.max_retries:
                    raise FECAPIError('Unable to reach the FEC API.') from exc
                time.sleep(self.backoff_seconds * (2 ** attempt))
                continue

            self._last_request_at = time.monotonic()

            if response.status_code == 403:
                raise FECAPIForbidden('FEC API rejected the configured API key.')
            if response.status_code == 429:
                raise FECAPIRateLimitError('FEC API rate limit exceeded.')
            if response.status_code != 200:
                logger.warning(
                    'Retrying FEC API endpoint=%s status=%s attempt=%s',
                    endpoint,
                    response.status_code,
                    attempt + 1,
                )
                if attempt >= self.max_retries:
                    raise FECAPIError(f'FEC API returned status {response.status_code}.')
                time.sleep(self.backoff_seconds * (2 ** attempt))
                continue

            return response.json()

        raise FECAPIError('FEC API request retries were exhausted.')

    def list_candidates(
        self,
        office: str,
        state: str | None,
        cycle: int,
        page: int = 1,
    ) -> dict:
        params = {
            'office': office,
            'election_year': cycle,
            'per_page': 100,
            'page': page,
        }
        if office != 'P' and state:
            params['state'] = state
        return self._request('/candidates/', params)

    def list_candidates_all_pages(
        self,
        office: str,
        state: str | None,
        cycle: int,
    ) -> list[dict]:
        page = 1
        candidates: list[dict] = []

        while True:
            payload = self.list_candidates(office=office, state=state, cycle=cycle, page=page)
            candidates.extend(payload.get('results', []))
            total_pages = payload.get('pagination', {}).get('pages') or page
            if page >= total_pages:
                break
            page += 1

        return candidates
