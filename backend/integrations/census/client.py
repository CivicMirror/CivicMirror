import logging
import time

import requests

logger = logging.getLogger(__name__)


class CensusGeocoderClient:
    BASE_URL = 'https://geocoding.geo.census.gov/geocoder/geographies/address'
    ZIP_URL = 'https://geocoding.geo.census.gov/geocoder/geographies/address'

    def __init__(self):
        self.timeout = 10
        self.max_retries = 3
        self.backoff_seconds = 1.0
        self.session = requests.Session()

    def _request(self, url: str, params: dict) -> dict | None:
        time.sleep(1)

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
            except requests.RequestException as exc:
                logger.warning('Census geocoder request failed on attempt %s: %s', attempt + 1, exc)
                if attempt >= self.max_retries:
                    return None
                time.sleep(self.backoff_seconds * (2 ** attempt))
                continue

            if response.status_code in {429, 503} or 500 <= response.status_code < 600:
                logger.warning(
                    'Retrying Census geocoder status=%s attempt=%s params=%s',
                    response.status_code,
                    attempt + 1,
                    {key: value for key, value in params.items() if key != 'street'},
                )
                if attempt >= self.max_retries:
                    return None
                time.sleep(self.backoff_seconds * (2 ** attempt))
                continue

            try:
                response.raise_for_status()
                return response.json()
            except (requests.RequestException, ValueError) as exc:
                logger.warning('Unable to decode Census geocoder response: %s', exc)
                return None

        return None

    def geocode_address(self, street: str, city: str, state: str, zip_code: str = '') -> dict | None:
        """
        Call Census Geocoder with address fields.
        Returns raw response dict or None on failure.
        Params: street, city, state, benchmark='Public_AR_Current', vintage='Current_Current', format='json'
        Throttle: 1 request per second (use time.sleep(1))
        """
        params = {
            'street': street,
            'city': city,
            'state': state,
            'benchmark': 'Public_AR_Current',
            'vintage': 'Current_Current',
            'format': 'json',
        }
        if zip_code:
            params['zip'] = zip_code
        return self._request(self.BASE_URL, params)

    def geocode_zip(self, zip_code: str) -> dict | None:
        """
        Approximation: geocode the ZIP centroid by using the ZIP as a city approximation.
        Use params: street='1 Main St', city=zip_code, state='', zip=zip_code
        Mark result as approximate.
        Returns raw response dict or None.
        """
        payload = self._request(
            self.ZIP_URL,
            {
                'street': '1 Main St',
                'city': zip_code,
                'state': '',
                'zip': zip_code,
                'benchmark': 'Public_AR_Current',
                'vintage': 'Current_Current',
                'format': 'json',
            },
        )
        if payload is not None:
            payload['approximate'] = True
        return payload
