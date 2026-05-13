class MatchConflictError(Exception):
    """Raised when a match is found but has irreconcilable conflicts."""


class AmbiguousMatchError(Exception):
    """Raised when multiple candidates could match and cannot be disambiguated."""


class NoRaceFoundError(Exception):
    """Raised when no matching race exists for an enrichment-only source."""
