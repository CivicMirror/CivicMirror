import hashlib
import logging
import time

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class CivicAPIError(Exception):
    pass


class CivicAPIForbidden(CivicAPIError):
    pass


class CivicAPIRetryableError(CivicAPIError):
    pass


class CivicAPIClient:
    BASE_URL = "https://www.googleapis.com/civicinfo/v2"

    def __init__(self):
        self.api_key = settings.CIVIC_API_KEY
        self.base_url = getattr(settings, "CIVIC_API_BASE", self.BASE_URL).rstrip("/")
        self.timeout = getattr(settings, "CIVIC_HTTP_TIMEOUT_SECONDS", 10)
        self.max_retries = getattr(settings, "CIVIC_MAX_RETRIES", 3)
        self.backoff_seconds = getattr(settings, "CIVIC_RETRY_BACKOFF_SECONDS", 1.0)
        self.session = requests.Session()

    def _address_hash(self, address: str) -> str:
        return hashlib.sha256(address.strip().lower().encode("utf-8")).hexdigest()[:12]

    def _request(self, endpoint: str, params: dict, *, allow_empty_400: bool = False, address: str = "") -> dict:
        if not self.api_key:
            raise CivicAPIForbidden("CIVIC_API_KEY is not configured.")

        merged_params = {**params, "key": self.api_key}
        address_hash = self._address_hash(address) if address else ""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(url, params=merged_params, timeout=self.timeout)
            except requests.RequestException as exc:
                if attempt >= self.max_retries:
                    raise CivicAPIRetryableError("Unable to reach the Civic API.") from exc
                time.sleep(self.backoff_seconds * (2 ** attempt))
                continue

            if response.status_code == 403:
                raise CivicAPIForbidden("Civic API rejected the configured API key.")

            if response.status_code == 400 and allow_empty_400:
                logger.info(
                    "Civic API returned no data for election=%s address_hash=%s",
                    params.get("electionId"),
                    address_hash,
                )
                return {}

            if response.status_code in {429, 503} or 500 <= response.status_code < 600:
                logger.warning(
                    "Retrying Civic API endpoint=%s status=%s election=%s address_hash=%s attempt=%s",
                    endpoint,
                    response.status_code,
                    params.get("electionId"),
                    address_hash,
                    attempt + 1,
                )
                if attempt >= self.max_retries:
                    raise CivicAPIRetryableError(f"Civic API returned retryable status {response.status_code}.")
                time.sleep(self.backoff_seconds * (2 ** attempt))
                continue

            response.raise_for_status()
            return response.json()

        raise CivicAPIRetryableError("Civic API request retries were exhausted.")

    def list_elections(self) -> list[dict]:
        payload = self._request("elections", {})
        elections = payload.get("elections", [])
        return [
            {
                "source_id": str(item.get("id", "")),
                "name": item.get("name", ""),
                "election_date": item.get("electionDay"),
                "ocd_division_id": item.get("ocdDivisionId", ""),
            }
            for item in elections
        ]

    def get_voter_info(self, address: str, election_id: str) -> dict:
        return self._request(
            "voterinfo",
            {"address": address, "electionId": election_id},
            allow_empty_400=True,
            address=address,
        )
