from __future__ import annotations

import csv
import io
import logging
import time
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

ETAG_CACHE_KEY_PREFIX = 'openelections:etag:'
DATA_CACHE_KEY_PREFIX = 'openelections:data:'
DATA_CACHE_TTL = 60 * 60 * 24 * 7  # 7 days


class OpenElectionsError(Exception):
    pass


class OpenElectionsClient:
    GITHUB_API = 'https://api.github.com'
    ORG = 'openelections'
    REPO_TEMPLATE = 'openelections-data-{state}'

    def __init__(self):
        self.token = getattr(settings, 'GITHUB_TOKEN', '')
        self.timeout = getattr(settings, 'CIVIC_HTTP_TIMEOUT_SECONDS', 10)
        self.max_retries = getattr(settings, 'CIVIC_MAX_RETRIES', 3)
        self.backoff_seconds = getattr(settings, 'CIVIC_RETRY_BACKOFF_SECONDS', 1.0)
        self.session = requests.Session()

    def list_result_files(self, state: str, since_sha: str | None = None) -> list[dict]:
        state = (state or '').lower()
        if since_sha:
            changed_paths = self._compare_changed_paths(state, since_sha)
            if changed_paths is not None:
                files: list[dict] = []
                for path in changed_paths:
                    if not path.lower().endswith('.csv'):
                        continue
                    metadata = self._get_contents(state, path)
                    if isinstance(metadata, dict) and metadata.get('type') == 'file':
                        files.append(
                            {
                                'path': metadata.get('path') or path,
                                'sha': metadata.get('sha') or '',
                                'download_url': metadata.get('download_url') or '',
                            }
                        )
                return files
        return self._walk_contents(state)

    def download_csv(self, download_url: str) -> list[dict]:
        response = self._request(download_url, accept='text/csv')
        response.raise_for_status()
        payload = response.content.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(payload))
        return [dict(row) for row in reader]

    def get_latest_commit_sha(self, state: str) -> str | None:
        state = (state or '').lower()
        payload = self._get_json(f'/repos/{self._repo(state)}/commits', params={'per_page': 1})
        if not isinstance(payload, list) or not payload:
            return None
        return str(payload[0].get('sha') or '').strip() or None

    def _compare_changed_paths(self, state: str, since_sha: str) -> list[str] | None:
        latest_sha = self.get_latest_commit_sha(state)
        if not latest_sha or latest_sha == since_sha:
            return []
        try:
            payload = self._get_json(f'/repos/{self._repo(state)}/compare/{since_sha}...{latest_sha}')
        except OpenElectionsError:
            logger.warning('Falling back to full contents listing for state=%s since_sha=%s', state, since_sha)
            return None
        files = payload.get('files') if isinstance(payload, dict) else []
        if not isinstance(files, list):
            return []
        return [
            str(item.get('filename') or '').strip()
            for item in files
            if str(item.get('filename') or '').strip() and item.get('status') != 'removed'
        ]

    def _walk_contents(self, state: str, path: str = '') -> list[dict]:
        contents = self._get_contents(state, path)
        if isinstance(contents, dict):
            contents = [contents]
        if not isinstance(contents, list):
            return []

        files: list[dict] = []
        for entry in contents:
            if not isinstance(entry, dict):
                continue
            entry_type = entry.get('type')
            entry_path = str(entry.get('path') or '').strip()
            if entry_type == 'dir' and entry_path:
                files.extend(self._walk_contents(state, entry_path))
                continue
            if entry_type == 'file' and entry_path.lower().endswith('.csv'):
                files.append(
                    {
                        'path': entry_path,
                        'sha': str(entry.get('sha') or '').strip(),
                        'download_url': str(entry.get('download_url') or '').strip(),
                    }
                )
        return files

    def _get_contents(self, state: str, path: str = ''):
        endpoint = f'/repos/{self._repo(state)}/contents'
        if path:
            endpoint = f'{endpoint}/{path.lstrip("/")}'
        return self._get_json(endpoint)

    def _get_json(self, endpoint: str, params: dict | None = None):
        url = self._build_url(endpoint, params)
        etag_key = f'{ETAG_CACHE_KEY_PREFIX}{url}'
        data_key = f'{DATA_CACHE_KEY_PREFIX}{url}'
        cached_etag = cache.get(etag_key)
        cached_data = cache.get(data_key)

        response = self._request(url, etag=cached_etag)
        if response.status_code == 304:
            return cached_data
        if response.status_code == 404:
            raise OpenElectionsError(f'GitHub resource not found: {url}')
        response.raise_for_status()
        payload = response.json()

        etag = response.headers.get('ETag')
        if etag:
            cache.set(etag_key, etag, DATA_CACHE_TTL)
        else:
            cache.delete(etag_key)
        cache.set(data_key, payload, DATA_CACHE_TTL)
        return payload

    def _request(self, url: str, *, etag: str | None = None, accept: str = 'application/vnd.github+json'):
        headers = {
            'Accept': accept,
            'X-GitHub-Api-Version': '2022-11-28',
        }
        if self.token:
            headers['Authorization'] = f'token {self.token}'
        if etag:
            headers['If-None-Match'] = etag

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(url, headers=headers, timeout=self.timeout)
            except requests.RequestException as exc:
                if attempt >= self.max_retries:
                    raise OpenElectionsError('Unable to reach the GitHub API.') from exc
                time.sleep(self.backoff_seconds * (2 ** attempt))
                continue

            if response.status_code == 403:
                raise OpenElectionsError('GitHub API request was rejected. Check GITHUB_TOKEN or rate limits.')
            if response.status_code == 404:
                return response
            if response.status_code == 304:
                return response
            if response.status_code >= 500:
                if attempt >= self.max_retries:
                    raise OpenElectionsError(f'GitHub API returned status {response.status_code}.')
                time.sleep(self.backoff_seconds * (2 ** attempt))
                continue
            return response

        raise OpenElectionsError('GitHub request retries were exhausted.')

    def _repo(self, state: str) -> str:
        return f'{self.ORG}/{self.REPO_TEMPLATE.format(state=state.lower())}'

    @staticmethod
    def _build_url(endpoint: str, params: dict | None = None) -> str:
        if endpoint.startswith('http://') or endpoint.startswith('https://'):
            base = endpoint
        else:
            base = f'{OpenElectionsClient.GITHUB_API.rstrip("/")}/{endpoint.lstrip("/")}'
        if not params:
            return base
        return f'{base}?{urlencode(sorted(params.items()))}'
