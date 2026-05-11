"""
Massachusetts Official Results Adapter
Source: https://electionstats.state.ma.us/
Feed quality: Moderate — machine-readable CSV/JSON exports available post-election.
Limitations:
  - Results often posted as CSV files; format varies by election cycle.
  - Unofficial results available night-of; certified final results within 10 days.
  - Write-ins reported as aggregate (no per-candidate breakdown).
  - No ranked-choice for state races.
"""
from __future__ import annotations

import datetime
import logging

from .base import AdapterResult, StateResultsAdapter
from .registry import register

logger = logging.getLogger(__name__)


@register
class MassachusettsAdapter(StateResultsAdapter):
    state = 'MA'
    SOURCE_URL = 'https://electionstats.state.ma.us/'

    def fetch_results(self, election_date: datetime.date, election_id: int) -> AdapterResult:
        logger.info('MA adapter: no automated feed available; returning empty result set')
        return AdapterResult(
            rows=[],
            source_url=self.SOURCE_URL,
            mapping_confidence='none',
            notes='MA results require manual CSV import. Automated feed not yet available.',
        )
