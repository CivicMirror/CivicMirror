import logging

import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)

LEGISLATORS_CURRENT_URL = 'https://theunitedstates.io/congress-legislators/legislators-current.json'
LEGISLATORS_HISTORICAL_URL = 'https://theunitedstates.io/congress-legislators/legislators-historical.json'
ETAG_CACHE_KEY_PREFIX = 'congress:etag:'
DATA_CACHE_KEY_PREFIX = 'congress:data:'
DATA_CACHE_TTL = 60 * 60 * 24 * 7  # 7 days


class CongressLegislatorsClient:
    def fetch_if_changed(self, url: str) -> tuple[list | None, bool]:
        """
        Download JSON array from url only if content has changed since last fetch.
        Use Django cache to store ETag and the data.
        Steps:
          1. Get cached ETag for this URL
          2. GET url with 'If-None-Match: <etag>' header if cached
          3. On 304 Not Modified: return (None, False) — unchanged
          4. On 200: cache new ETag and data, return (data, True)
          5. On error: log warning, return (None, False)
        Uses 10-second timeout, no retry needed (weekly schedule; failures retry next week).
        """
        etag_key = f'{ETAG_CACHE_KEY_PREFIX}{url}'
        data_key = f'{DATA_CACHE_KEY_PREFIX}{url}'
        cached_etag = cache.get(etag_key)
        headers = {'If-None-Match': cached_etag} if cached_etag else {}

        try:
            response = requests.get(url, headers=headers, timeout=10)
        except requests.RequestException as exc:
            logger.warning('Failed to fetch congress legislators url=%s: %s', url, exc)
            return None, False

        if response.status_code == 304:
            return None, False

        if response.status_code != 200:
            logger.warning('Congress legislators request failed url=%s status=%s', url, response.status_code)
            return None, False

        try:
            data = response.json()
        except ValueError as exc:
            logger.warning('Invalid congress legislators payload url=%s: %s', url, exc)
            return None, False

        if not isinstance(data, list):
            logger.warning('Unexpected congress legislators payload type url=%s type=%s', url, type(data).__name__)
            return None, False

        etag = response.headers.get('ETag')
        if etag:
            cache.set(etag_key, etag, DATA_CACHE_TTL)
        else:
            cache.delete(etag_key)
        cache.set(data_key, data, DATA_CACHE_TTL)
        return data, True

    def fetch_current(self) -> tuple[list | None, bool]:
        return self.fetch_if_changed(LEGISLATORS_CURRENT_URL)

    def fetch_historical(self) -> tuple[list | None, bool]:
        return self.fetch_if_changed(LEGISLATORS_HISTORICAL_URL)
