import logging
import re

import zipcodes

logger = logging.getLogger(__name__)

_ZIP_RE = re.compile(r'^\d{5}')


def resolve_state_from_zip(zip_code: str) -> str | None:
    """Return the two-letter US state abbreviation for a ZIP code, or None."""
    if not zip_code:
        return None
    cleaned = zip_code.strip()
    if not _ZIP_RE.match(cleaned):
        return None
    try:
        results = zipcodes.matching(cleaned[:5])
        return results[0]['state'] if results else None
    except Exception:
        logger.warning("ZIP lookup failed for %r", cleaned)
        return None
