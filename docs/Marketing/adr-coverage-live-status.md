# ADR-001: Coverage Page Live Sync Status

## Status
Proposed

## Context

The `/coverage` page currently displays a static tier breakdown (Full / Results / Elections) driven by a hardcoded constant in `frontend/src/utils/coverage.ts`. This tells visitors *which* states are covered but says nothing about *when* data was last pulled or *what* was collected.

### Requirements
- Visitors should be able to see how fresh the data is for each tier
- Returning visitors need a reason to check back after each nightly run
- The Coverage page should function as a credibility and trust signal for researchers / journalists evaluating CivicMirror
- The feature should be low-maintenance: no manual updates, no admin intervention
- Optional stretch goal: display what was actually pulled in the most recent run (record counts)

### Constraints
- The backend already has a `SyncLog` model (`backend/ops/models.py`) that records every sync run with `started_at`, `completed_at`, `status`, `source`, `records_created`, `records_updated`, and `records_skipped`
- The frontend is a React SPA (Vite + MUI); it cannot read the database directly
- The existing Coverage page is fully client-side rendered from `coverage.ts` constants; no API calls today
- The `source` field on `SyncLog` is a free-text string (e.g., `"wv_sos"`, `"civic"`, `"openelections"`); it is not formally typed against state codes, but state-specific sources follow a naming convention
- Must not introduce a new authentication requirement — the Coverage page is public

### Decision drivers
1. **Simplest backend surface area** — avoid introducing a complex new API; prefer a thin endpoint over a new Django app
2. **Resilience to sync failures** — if last night's sync failed or didn't run, the UI should degrade gracefully (show last-known timestamp, not an error state)
3. **Freshness, not volume** — the primary value is "when was this last updated," not detailed run statistics; volume is optional enrichment
4. **SEO / AI legibility** — the Coverage page is a target for "which states does CivicMirror cover" queries; adding last-synced data makes the page more valuable and more likely to be cited as authoritative

---

## Decision

**Add a lightweight public `GET /api/v1/coverage/sync-status/` endpoint** that aggregates the most recent completed `SyncLog` entry per source and returns a summary. The frontend Coverage page fetches this on load and overlays "Last synced: [time ago]" and optional record counts onto each state card.

### Endpoint contract

```
GET /api/v1/coverage/sync-status/
```

Response:
```json
{
  "as_of": "2026-06-14T03:22:17Z",
  "sources": {
    "wv_sos": {
      "last_completed_at": "2026-06-14T02:15:00Z",
      "status": "completed",
      "records_created": 0,
      "records_updated": 42,
      "records_skipped": 18
    },
    "co_sos": {
      "last_completed_at": "2026-06-14T02:18:00Z",
      "status": "completed",
      "records_created": 3,
      "records_updated": 97,
      "records_skipped": 5
    },
    "civic": {
      "last_completed_at": "2026-06-14T03:00:00Z",
      "status": "completed",
      "records_created": 12,
      "records_updated": 340,
      "records_skipped": 0
    }
  }
}
```

The `as_of` field is the server time at response generation. Each key under `sources` is a `SyncLog.source` value. The endpoint returns only entries where `status` is `completed` or `completed_with_warnings`; failed or in-progress runs are excluded from the "last completed" summary but a `latest_status` field can be added later if needed.

### Frontend behavior

- On Coverage page load, fetch `/api/v1/coverage/sync-status/` in a `useEffect`
- Map source names to state codes via a lookup table (e.g., `{ wv_sos: 'WV', co_sos: 'CO', ... }`)
- States with a dedicated source: display "Last synced [time ago]" on the state card
- States on the `civic` (national) source: display a shared "National feed last synced [time ago]" banner at the top of the Elections Only section
- If the fetch fails or times out: Coverage page renders exactly as today (graceful degradation, no error shown to user)
- No loading spinner on the cards; overlay appears after fetch resolves (avoids layout shift)

### Optional stretch: record counts

If the `records_created` + `records_updated` counts are non-zero and meaningful, display them:
- "Last synced 3h ago · 42 updated"
- Keep it minimal — the timestamp is the primary value; counts are enrichment

---

## Justification

1. **`SyncLog` already captures everything needed** — no new data model is required; the endpoint is a read-only aggregation query over existing data
2. **Public endpoint is appropriate** — sync timestamps are not sensitive; this information is relevant to the site's mission of transparency
3. **Graceful degradation is built in** — if the endpoint fails, nothing breaks; the Coverage page is static by default
4. **Encourages return visits** — a page that updates every night gives returning visitors and external linkers a reason to check back (marketing value: the Coverage page becomes a live dashboard, not a static brochure)
5. **Low implementation cost** — ~1 day backend (endpoint + Django REST serializer), ~half day frontend (fetch + overlay)

---

## Consequences

### Positive
- Coverage page becomes a live, self-updating signal of system health and data freshness
- Strengthens E-E-A-T signals for the page ("this data was updated 3 hours ago")
- Gives researchers and journalists a confidence signal that the data pipeline is running
- Creates a repeatable content event: "CivicMirror added [N] new races in WV last night" is linkable
- Backend engineers get an at-a-glance pipeline health check via the public endpoint

### Negative
- New API endpoint to maintain (minor — it's a thin read-only aggregation)
- Source-to-state-code mapping must be kept in sync as new adapters are added
- If `SyncLog.source` naming convention drifts, the mapping breaks silently — needs a note in the engineering onboarding docs

---

## Alternatives Considered

### Alternative 1: Static last-updated dates in `coverage.ts`
Manually update the coverage constants file whenever a sync runs.

Reason rejected: Not automated; requires manual intervention after every nightly run; will become stale within days.

### Alternative 2: Expose raw `SyncLog` records via existing admin / ops API

Use the existing `ops` app to expose full `SyncLog` records to the frontend.

Reason rejected: `SyncLog` records include internal fields (`task_name`, `error_count`, `last_error`) that are not appropriate to expose publicly without filtering. A dedicated thin endpoint is safer and easier to version.

### Alternative 3: Server-side render the Coverage page

Use Django templates or a Next.js SSR layer to render sync timestamps at request time.

Reason rejected: The frontend is a React SPA on Vite; introducing SSR is a significant architectural change that is out of scope. The client-side fetch approach achieves the same result with graceful degradation.

### Alternative 4: Push-based update via WebSocket

When a sync completes, push the new status to any open Coverage page sessions.

Reason rejected: Over-engineered for this use case. Sync runs nightly; a on-load fetch is sufficient. WebSocket infrastructure would add meaningful complexity.

---

## Implementation Notes

### Backend

New file: `backend/ops/views.py` — add a `CoverageSyncStatusView`:

```python
from django.db.models import Max, Subquery, OuterRef
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.utils import timezone
from .models import SyncLog


class CoverageSyncStatusView(APIView):
    permission_classes = [AllowAny]

    COMPLETED_STATUSES = {SyncLog.Status.COMPLETED, SyncLog.Status.COMPLETED_WITH_WARNINGS}

    def get(self, request):
        # Get latest completed log per source
        latest_per_source = (
            SyncLog.objects
            .filter(status__in=self.COMPLETED_STATUSES, source__gt='')
            .order_by('source', '-completed_at')
            .distinct('source')
        )

        sources = {}
        for log in latest_per_source:
            sources[log.source] = {
                'last_completed_at': log.completed_at,
                'status': log.status,
                'records_created': log.records_created,
                'records_updated': log.records_updated,
                'records_skipped': log.records_skipped,
            }

        return Response({
            'as_of': timezone.now(),
            'sources': sources,
        })
```

Wire to URL: `path('coverage/sync-status/', CoverageSyncStatusView.as_view())` in `api/urls.py`.

**Note:** The `distinct('source')` approach requires PostgreSQL (which CivicMirror uses). On SQLite (dev), use a manual Python-side dedup if needed.

### Frontend

New hook: `frontend/src/hooks/useCoverageSyncStatus.ts`

```typescript
import { useEffect, useState } from 'react';

interface SourceStatus {
  last_completed_at: string;
  status: string;
  records_created: number;
  records_updated: number;
  records_skipped: number;
}

interface SyncStatusResponse {
  as_of: string;
  sources: Record<string, SourceStatus>;
}

// Maps backend source keys to state codes
export const SOURCE_TO_STATE: Record<string, string> = {
  wv_sos: 'WV',
  co_sos: 'CO',
  sc_sos: 'SC',
  ma_sos: 'MA',
  va_sos: 'VA',
  az_sos: 'AZ',
  nc_sos: 'NC',
  // Results adapter sources
  ar_results: 'AR',
  ct_results: 'CT',
  // ... extend as adapters are added
};

export function useCoverageSyncStatus() {
  const [status, setStatus] = useState<SyncStatusResponse | null>(null);

  useEffect(() => {
    fetch('/api/v1/coverage/sync-status/')
      .then((r) => r.ok ? r.json() : null)
      .then((data: SyncStatusResponse | null) => { if (data) setStatus(data); })
      .catch(() => { /* silently degrade */ });
  }, []);

  return status;
}
```

In `CoveragePage.tsx`, call `useCoverageSyncStatus()` and pass status into `StateCard` for display.

---

## Decision Record

| | |
|---|---|
| **Decided by** | Walter LeFort |
| **Date** | 2026-06-14 |
| **Status** | Proposed |
| **Supersedes** | — |
| **Related ADRs** | — |

---

*See also: `marketing-plan.md` §6 (Retention) · `seo-plan.md` §2.4 (Coverage page SEO)*
