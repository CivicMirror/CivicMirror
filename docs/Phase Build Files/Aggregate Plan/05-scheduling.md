# Scheduling — Celery Beat Tasks and Rate-Limit Strategy

> **Status: ✅ IMPLEMENTED** — All tasks wired in `backend/config/celery.py`. OpenElections fan-out wrapper included with graceful degradation if module not yet loaded.

## Overview

This document specifies the Celery beat schedule for all new background sync tasks, rate-limit policies for each source, and incremental sync strategy to stay within free-tier API limits.

---

## Celery Beat Schedule (add to `config/settings.py` or `celery.py`)

| Task | Schedule | Scope | Notes |
|---|---|---|---|
| `sync_elections` (existing) | Every 6 hours | All active elections | No change |
| `sync_election_races` (existing) | Triggered by sync_elections | Per election | No change |
| `sync_fec_candidates` | Nightly 2 AM UTC | Current + upcoming federal cycle | Paginated per state per office |
| `sync_congress_legislators` | Weekly Sunday 3 AM UTC | Full legislators-current.json | ETag/checksum skip if unchanged |
| `sync_openstates_legislators` | Nightly 4 AM UTC | All states, 1 state per minute | Rate-limit fan-out via countdown |
| `refresh_district_records` | Monthly | Full OCD + TIGER refresh | Heavy; monthly is sufficient |
| `check_openelections_new_results` | Weekly Saturday midnight | New CSV detection per state | Admin or auto-trigger on detection |
| `ingest_openelections_state` | Post-detection trigger | Per state per election year | Admin-confirmed or auto if high confidence |
| `ingest_medsl_results` | Manual / post-election | Per dataset | Large import; manual trigger preferred |

---

## Rate-Limit Policies Per Source

### Google Civic API (existing)
- 25,000 requests/day on free tier
- Already handled in `integrations/civic/client.py` with retry/backoff
- No changes needed

### OpenFEC API
- **Free tier:** 1,000 requests/hour
- **Strategy:**
  - Max page size: 100 records per page
  - Throttle: 1 request per 4 seconds maximum (`time.sleep(4)` between pages)
  - Estimated requests per nightly run: ~200–500 (50 states × 2 offices × 2–5 pages average)
  - Within limits; no quota concerns for typical election cycles
- **Incremental strategy:**
  - Use `SourceRecord` checksum: skip records whose payload hasn't changed
  - Store FEC `last_file_date` in `SyncLog` to detect new filings
  - Sync only current + 1 upcoming cycle (not all historical)

```python
# Example rate limiting in fec/client.py
import time

class FECClient:
    MIN_REQUEST_INTERVAL = 4.0  # seconds between requests

    def _request(self, endpoint, params):
        time.sleep(self.MIN_REQUEST_INTERVAL)
        # ... existing retry logic pattern ...
```

### congress-legislators (GitHub raw files)
- No API key needed
- No rate limits for direct file download
- Use HTTP `ETag` or `Last-Modified` caching to avoid re-downloading unchanged files
- Weekly schedule is conservative; could be daily without concern

```python
# Incremental check in congress/client.py
def fetch_if_changed(url: str, cached_etag: str | None) -> tuple[list | None, str]:
    headers = {}
    if cached_etag:
        headers['If-None-Match'] = cached_etag
    response = requests.get(url, headers=headers)
    if response.status_code == 304:
        return None, cached_etag  # unchanged
    new_etag = response.headers.get('ETag', '')
    return response.json(), new_etag
```

### Open States API
- **Free tier:** 500 requests/day
- **Strategy:**
  - 50 states × ~3–5 pages each = ~150–250 requests per full sync
  - Use Celery `countdown` to fan out states over the sync window: 1 state per minute
  - Sync each state once per nightly run; skip if `SyncLog` shows success in last 20 hours
  - `per_page=50` (max allowed)

```python
# In openstates/tasks.py — fan out states with delay
@shared_task
def sync_openstates_all_states():
    for i, state in enumerate(US_STATES):
        sync_openstates_legislators.apply_async(
            args=[state],
            countdown=i * 60,  # 1 state per minute
        )
```

- **Incremental strategy:** Use `SourceRecord` checksum; skip unchanged person records

### U.S. Census Geocoder
- No API key; no enforced rate limits
- Throttle courtesy: 1 request per second for bulk resolution
- District records cached in `DistrictRecord` model; resolution only re-runs on monthly refresh task
- For real-time address lookups (per user request), use in-memory cache with 24-hour TTL

### OpenElections (GitHub)
- No API key; GitHub API unauthenticated = 60 requests/hour
- Use GitHub authenticated requests if more throughput needed (`GITHUB_TOKEN` from env)
- Weekly check scans for new CSV files by checking commit timestamps
- Full file download only for new or changed files
- **Incremental strategy:** Track `last_processed_commit_sha` per state repo in `SyncLog`

---

## Incremental Sync Strategy Summary

The key mechanism for keeping all syncs efficient and within rate limits is **checksum-based skipping**:

1. Before processing any raw record, call `SourceRecordStore.upsert()`
2. If `changed=False`, increment `records_skipped` and move on
3. Only records with changed payloads go through the full match/enrich pipeline
4. This means nightly runs that find no new data complete quickly and cheaply

---

## Sync Order Dependencies

Some tasks depend on others. Celery beat should schedule them in this order within the same nightly window:

```
1. sync_fec_candidates (2 AM UTC)
         ↓
2. sync_congress_legislators (3 AM UTC)
         ↓
3. sync_openstates_legislators fan-out (4 AM UTC → 5 AM UTC)
         ↓
4. All above feed orchestrator enrichment before morning traffic
```

`refresh_district_records` (monthly) and `check_openelections_new_results` (weekly) can run independently.

---

## Error Handling and Retry Policy

All new tasks follow the same pattern as the existing Civic tasks:

```python
@shared_task(bind=True, max_retries=3)
def sync_fec_candidates(self, cycle_year: int):
    try:
        # ... sync logic ...
    except RateLimitExceeded as exc:
        # Back off longer on rate limit
        raise self.retry(exc=exc, countdown=300)  # 5 minutes
    except NetworkError as exc:
        raise self.retry(exc=exc, countdown=_backoff(self.request.retries))
    except Exception as exc:
        sync_log.status = SyncLog.Status.FAILED
        sync_log.last_error = str(exc)
        sync_log.save(...)
        raise
```

Rate-limit errors get a 5-minute backoff. Network errors get exponential backoff (1s, 2s, 4s). All tasks log to `SyncLog` regardless of outcome.

---

## Monitoring

The existing `SyncLog` model already provides a Django admin view of sync history. After implementation, the following fields give visibility into the new syncs:

- `source` — `fec`, `congress`, `openstates`, `census`, `openelections`, `medsl`
- `records_created` / `records_updated` / `records_skipped` — volume per run
- `error_count` / `last_error` — failure details
- `status` — `completed`, `completed_with_warnings`, `failed`

For production, a simple admin dashboard widget showing last-sync status per source is recommended.

---

## Next Document

[06-api-keys.md](06-api-keys.md) — API key status and acquisition guide.
