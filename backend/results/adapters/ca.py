"""
California Official Results Adapter
Source: https://www.sos.ca.gov/elections/
Feed quality: Variable — county-level reporting; no unified statewide machine-readable feed.
Limitations:
  - California reports results at the county level with 58 different county formats.
  - Statewide race aggregation requires merging county feeds.
  - Write-ins reported as aggregate per county.
  - Certified results 30+ days post-election.
  - High structural diversity stresses adapter flexibility.
"""
from __future__ import annotations

import datetime
import logging

from .base import AdapterResult, StateResultsAdapter
from .registry import register

logger = logging.getLogger(__name__)


@register
class CaliforniaAdapter(StateResultsAdapter):
    state = 'CA'
    SOURCE_URL = 'https://www.sos.ca.gov/elections/'

    def fetch_results(self, election_date: datetime.date, election_id: int) -> AdapterResult:
        logger.info('CA adapter: county-level aggregation required; returning stub result set')
        return AdapterResult(
            rows=[],
            source_url=self.SOURCE_URL,
            mapping_confidence='partial',
            notes='CA results require aggregating 58 county feeds. Adapter skeleton ready; per-county URL patterns needed.',
        )
