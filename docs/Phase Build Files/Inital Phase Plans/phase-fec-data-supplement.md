# Phase FEC Data Supplement

## Problem
The project already has Google Civic ingestion and a local cache, but Civic coverage is incomplete. We need a fallback chain that preserves the current UI flow, uses FEC for federal gaps, and keeps any existing state/local data sources in the lookup path when available.

## Proposed approach
1. Preserve the current request flow as the primary path: user selects location, backend checks local cache and Google Civic data first.
2. For federal elections, add an FEC fallback branch that runs only after Civic returns no usable data.
3. For state/local elections, keep the Civic/local-cache path and also route through any existing local data source already available in the project before returning no data.
4. Normalize successful fallback payloads into the existing local cache/update pipeline so later lookups can reuse the same data path.
5. Return a clear "No Data found" message only after every available source in the chain has failed.

## Planned work
- Review current backend Civic task/client/cache flow and identify the exact insertion point for the fallback orchestrator.
- Inventory any existing local/state data sources already in the app so the plan can place them correctly in the miss chain.
- Add an FEC client/service that reads the configured API key from secrets/environment and uses the same timeout/retry/error posture as Civic.
- Extend the backend selection flow so lookups can:
  - check local cache
  - query Google Civic
  - query FEC for federal misses
  - query any available local/state source for non-federal misses
  - persist successful fallback results into the local cache/update process
- Define the mapping from FEC election data into the project's local cache/data model.
- Add backend tests for:
  - Civic hit
  - Civic miss + FEC hit
  - Civic miss + local/state hit
  - total miss returning "No Data found"
  - cache write after fallback success

## Notes
- FEC is still federal-only; the plan should not assume it can replace Civic for all scopes.
- The repository already has Civic client/cache/task code and a public/local-race path, so the implementation should slot into the existing flow instead of introducing a parallel one.
