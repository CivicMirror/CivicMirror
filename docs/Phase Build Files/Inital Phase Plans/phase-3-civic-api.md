# Phase 3 Google Civic API Ingestion

## Goal
Wire CivicMirror to the Google Civic API so the platform can import real elections and races, while explicitly accounting for the API's address-based coverage limitation before race browsing depends on it.

## Prerequisites
- Phase 1 Foundation complete
- Phase 2 Authentication complete for admin/ops access, even though public browsing remains open

### Environment and application configuration
Add environment-driven Civic integration settings:
- `CIVIC_API_KEY` — sourced from GCP Secret Manager in production, mounted as an environment variable to the Cloud Run service; use a local `.env` file for development
- `CIVIC_API_BASE` (default Google Civic API base URL)
- Optional but useful:
  - `CIVIC_HTTP_TIMEOUT_SECONDS`
  - `CIVIC_MAX_RETRIES`
  - `CIVIC_RETRY_BACKOFF_SECONDS`

Keep all Civic settings in a dedicated config module so Celery tasks and admin-triggered syncs share the same values.

### CivicAPIClient design
Create a `CivicAPIClient` service class with methods:
- `list_elections()`
- `get_voter_info(address, election_id)`

Implementation requirements:
- explicit request timeout
- retry policy for transient failures
- backoff handling for rate limits and 5xxs
- structured logging with request outcome, election id, and retry count
- no logging of raw user-provided address strings

Recommended client behavior:
- `list_elections()` returns normalized election payloads or DTOs, not raw view-layer dicts
- `get_voter_info()` accepts an address string plus `election_id`, calls `voterInfoQuery`, and normalizes contests, candidates, and district metadata

### Coverage strategy spike
This is a core product/technical decision and must be documented before building the browser.

Constraint:
- Google Civic `/elections` can list available elections, but `voterInfoQuery` requires both an address and an `electionId`.
- There is no reliable global endpoint that returns every race for an election without an address.

Chosen Phase 3 strategy:
- Seed initial race coverage with a representative address set per state.
- Start with at least:
  - state capital address
  - largest city address
- For large or high-priority states, optionally add one suburban and one rural representative address.
- Store representative addresses in internal seed/config data for import jobs only.
- Expand coverage on demand when a user searches by their own address later.
- Do not persist raw end-user addresses in the relational database.

Operational implication:
- The stored Civic import corpus is a growing cache of discovered races, not a guaranteed complete snapshot of every ballot in the country.
- UI copy and product expectations should reflect this reality.

### Election import mapping
Implement election sync that maps Google Civic election payloads into `Election` rows.

Map at minimum:
- Civic `id` → `Election.source_id`
- Civic `name` → `Election.name`
- Civic election date → `Election.election_date`
- Parse `ocdDivisionId` when present to infer:
  - `state`
  - `jurisdiction_level`
- Set `status` based on election date and later certification lifecycle

Import behavior:
- use `update_or_create(source_id=...)`
- do not duplicate the same election across repeated syncs
- archive or mark stale elections rather than deleting historical records

### Race import mapping from contests
Map each normalized contest into `Race`.

Required mapping rules:
- `contest.type == "Referendum"` → `race_type = measure`
- everything else → `race_type = candidate`
- `contest.office` → `office_title`
- jurisdiction info from contest metadata → `jurisdiction`
- `contest.district.scope` → `geography_scope`
- derive `voting_opens` / `voting_closes` from the parent election window or configured defaults if the API does not provide exact times
- `source = civic_api`
- `race_status = active` for publicly available imported races

Persist additional import metadata where available:
- `ocd_division_id`
- normalized office title
- canonical key inputs

### Candidate import mapping
For candidate contests:
- map `contest.candidates[]` into `Candidate`
- capture:
  - `name`
  - `party`
  - `incumbent`
- default `candidate_status = running` unless import metadata indicates otherwise

Use idempotent writes keyed by race + normalized candidate name so repeated imports do not fan out duplicates.

### MeasureOption creation
For measure races:
- create `MeasureOption` rows for:
  - `Yes`
  - `No`
  - `Abstain`
- keep these deterministic so frontend rendering and vote-casting validation are simple
- avoid recreating options on repeated syncs

### Dedup and canonical key strategy
The code review critique is correct: simple title matching is not enough.

Canonical key format should be based on:
- `source`
- `Election.source_id`
- normalized office title
- `ocd_division_id`
- `race_type`
- `Election.election_date`

Recommended implementation:
- compute a `canonical_key` string during import
- enforce uniqueness on `Race.canonical_key`
- use `update_or_create(canonical_key=...)`

Fallback compatibility rule:
- if `ocd_division_id` is missing, fall back to normalized office title + jurisdiction + election date, but log that the match confidence is weaker

### Two-layer caching strategy
User-driven address queries grow the race database organically — every new address that hits the Civic API seeds races that all future users in that area benefit from. Caching happens at two layers:

**Layer 1 — Redis (hot deduplication, 1 hr TTL)**
Cache the raw Civic API `voterInfoQuery` response keyed by `hash(normalized_address + election_id)`. Prevents duplicate API hits for the same address within a short window (e.g. two users on the same street within the hour).

**Layer 2 — Database staleness (dynamic TTL)**
Each `Race` or `Election` record tracks `last_synced_at`. Before hitting the Civic API for an address query, check whether the races for that jurisdiction are fresh enough. TTL is dynamic based on how close the election is:

```python
def get_race_ttl(election_date):
    days_until = (election_date - date.today()).days
    if days_until > 30:  return timedelta(hours=48)
    if days_until > 7:   return timedelta(hours=24)
    if days_until > 1:   return timedelta(hours=6)
    return timedelta(hours=1)  # election day
```

| Phase | Days to election | DB refresh TTL | Reason |
|---|---|---|---|
| Off-cycle | > 30 days | 48 hrs | Race info barely changes |
| Active cycle | 7–30 days | 24 hrs | Candidate withdrawals/filings |
| Election week | 1–7 days | 6 hrs | Last-minute changes more likely |
| Election day | 0 days | 1 hr | Polling location updates possible |
| Post-election | Past | N/A | Switch to results ingestion (Phase 7) |

**Request flow:**
```
User query (address + election_id)
        │
        ▼
Redis hit? ──YES──→ return cached API response (1 hr)
        │ NO
        ▼
DB races fresh? (last_synced_at within dynamic TTL) ──YES──→ return from DB
        │ NO / never seeded
        ▼
Hit Civic API → persist races to DB (update last_synced_at)
             → cache response in Redis (1 hr)
             → return results
```

**Quota note:** Google Civic API free tier allows 25,000 requests/day. Because the cache keys on jurisdiction rather than individual addresses, API calls scale with new *jurisdictions* discovered, not new *users*. Once a congressional district is seeded, every address in it is served from DB.

### Celery and Redis setup
Use Celery with Redis to keep Civic syncing out of request/response paths.

Required pieces:
- `CELERY_BROKER_URL` from Redis
- `CELERY_RESULT_BACKEND` if task result inspection is needed
- Celery app wiring in Django startup
- beat schedule runs hourly — the dynamic TTL logic inside `sync_election_races` skips any race whose `last_synced_at` is still fresh, so running the beat frequently is safe and ensures election-week/election-day TTLs (6 hr / 1 hr) are actually honoured
- task routing so Civic sync jobs can be isolated from future results-ingestion jobs if queues split later

### Sync tasks
Create tasks with explicit retry posture:
- `sync_elections()`
- `sync_election_races(election_id, address)`

Task expectations:
- `bind=True`
- `max_retries=3`
- exponential backoff on retryable errors
- record counts of created and updated objects
- capture partial failures without hiding them

Suggested flow:
1. `sync_elections()` refreshes the election list.
2. For each target election and representative address, queue `sync_election_races(election_id, address)`.
3. Each race sync imports races, candidates, and measure options idempotently.

### Import observability with SyncLog
Create a `SyncLog` model for operational visibility with fields:
- `election`
- `started_at`
- `completed_at`
- `records_created`
- `records_updated`
- `error_count`
- `last_error`
- Recommended additions:
  - `source`
  - `task_name`
  - `address_label` or representative-address identifier, not raw address
  - `status` (`started`, `completed`, `completed_with_warnings`, `failed`)

Expose `SyncLog` in Django admin for support and import audits.

### Error handling matrix
Handle Civic API responses intentionally:

| HTTP status | Meaning in CivicMirror | Action |
| --- | --- | --- |
| 400 | No contests or bad address/election combination | If caused by no contests for a representative address, record zero imports and do not treat as a fatal sync error |
| 403 | Invalid or unauthorized API key | Raise immediately, fail the task, alert ops |
| 429 | Rate limited | Retry with exponential backoff |
| 503 | Upstream unavailable | Retry with exponential backoff |

Additional rule:
- distinguish "no contests returned" from true client misuse so dashboards do not exaggerate failures

### Admin and operator workflows
- Add admin actions to trigger election syncs manually.
- Add a SyncLog admin view with filters for election, status, and time range.
- Show summary counters so operators can quickly detect broken API credentials or widening 429 patterns.

## Deliverables Checklist
- [ ] Civic API environment variables defined and loaded through Django settings
- [ ] `CivicAPIClient` implemented with `list_elections()` and `get_voter_info(address, election_id)`
- [ ] Retry, timeout, and rate-limit handling added to Civic API calls
- [ ] Coverage strategy documented and implemented with representative addresses plus on-demand expansion
- [ ] Election import maps Civic data into `Election` records idempotently
- [ ] Contest import maps Civic contests into `Race` records with correct race types and metadata
- [ ] Candidate contests import into `Candidate` records without duplication
- [ ] Referendum contests generate deterministic `Yes/No/Abstain` `MeasureOption` rows
- [ ] Canonical race dedup strategy implemented using a persisted unique key
- [ ] Two-layer caching implemented: Redis (1 hr hot dedup) + DB staleness check with dynamic TTL based on days to election
- [ ] `last_synced_at` tracked on Election/Race records and used to gate Civic API calls
- [ ] Celery and Redis configured for scheduled and manual Civic sync tasks
- [ ] `sync_elections()` and `sync_election_races(election_id, address)` created with retries and backoff
- [ ] `SyncLog` model and Django admin view provide import observability
- [ ] Civic API error handling follows the documented 400/403/429/503 matrix
