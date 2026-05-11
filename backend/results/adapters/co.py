"""
Colorado Official Results Adapter
Source: https://www.sos.state.co.us/pubs/elections/results/
Feed quality: Good — Colorado Secretary of State publishes structured result exports.
Limitations:
  - JSON/XML exports have a stable structure but API endpoint changes per election cycle.
  - Ranked-choice races (e.g. some local elections) include round data.
  - Certified results typically available 2-3 weeks post-election.
"""
from __future__ import annotations

import datetime
import logging

from .base import AdapterResult, StateResultsAdapter
from .registry import register

logger = logging.getLogger(__name__)


@register
class ColoradoAdapter(StateResultsAdapter):
    state = 'CO'
    SOURCE_URL = 'https://www.sos.state.co.us/pubs/elections/results/'

    def fetch_results(self, election_date: datetime.date, election_id: int) -> AdapterResult:
        logger.info('CO adapter: election-specific URL required; returning stub result set')
        return AdapterResult(
            rows=[],
            source_url=self.SOURCE_URL,
            mapping_confidence='partial',
            notes='CO adapter requires election-specific SoS URL. Feed structure ready for integration once URL pattern confirmed.',
        )
