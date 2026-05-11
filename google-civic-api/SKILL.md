---
name: google-civic-api
description: Guidelines for integrating the Google Civic Information API into CivicMirror — covering election sync, voterInfoQuery, address-based race filtering, data mapping to Django models, and Celery scheduling patterns.
---

# Google Civic Information API — CivicMirror Skill

## When to use

Use this skill when working on any feature in CivicMirror that touches:
- Importing or syncing elections and races from the Google Civic API
- Resolving races from a ZIP code, address, or state filter
- Mapping Civic API response fields to CivicMirror's Django models
- Writing or updating the Celery sync task
- Handling API errors, rate limits, or missing data gracefully

---

## API Overview

Base URL: `https://www.googleapis.com/civicinfo/v2`
Auth: API key via `?key=API_KEY` query parameter (never commit the key — use environment variable `CIVIC_API_KEY`)

### Key endpoints used by CivicMirror

| Endpoint | Method | Purpose |
|---|---|---|
| `/elections` | GET | List all upcoming and recent elections |
| `/voterinfo` | GET | Races, candidates, and polling info for an address |
| `/representatives` | GET | Elected officials by address (future use) |

---

## Endpoint Details

### 1. `GET /elections`

Returns all known upcoming elections across all states.

```
GET https://www.googleapis.com/civicinfo/v2/elections?key={API_KEY}
```

Response shape:
```json
{
  "elections": [
    {
      "id": "9000",
      "name": "2026 Massachusetts General Election",
      "electionDay": "2026-11-03",
      "ocdDivisionId": "ocd-division/country:us/state:ma"
    }
  ]
}
```

Use for: populating the `Election` model during scheduled sync. Map `id` → `source_id`, `name` → `name`, `electionDay` → `election_date`, parse `ocdDivisionId` for `state` and `jurisdiction_level`.

---

### 2. `GET /voterinfo`

Returns contests (races), candidates, and ballot measures for a specific address.

```
GET https://www.googleapis.com/civicinfo/v2/voterinfo
  ?key={API_KEY}
  &address={URL_ENCODED_ADDRESS}
  &electionId={ELECTION_ID}
```

Use `address` with a full street address, city, state, and ZIP. For ZIP-only queries, use `{ZIP} USA` as the address string.

Response shape (simplified):
```json
{
  "election": { "id": "...", "name": "...", "electionDay": "..." },
  "contests": [
    {
      "type": "General",
      "office": "U.S. Senate",
      "district": { "name": "Massachusetts", "scope": "statewide" },
      "candidates": [
        { "name": "Jane Smith", "party": "Democratic" },
        { "name": "John Doe",  "party": "Republican" }
      ],
      "primaryParty": null,
      "referendumTitle": null,
      "referendumSubtitle": null,
      "referendumText": null
    },
    {
      "type": "Referendum",
      "referendumTitle": "Question 2",
      "referendumSubtitle": "...",
      "referendumText": "Full ballot measure text..."
    }
  ]
}
```

Use for: populating `Race` and `Candidate` / `MeasureOption` models per election.

**Determining race_type:**
- `contest.type == "Referendum"` → `race_type = "measure"`, create `MeasureOption` rows for Yes/No/Abstain
- All other `contest.type` values → `race_type = "candidate"`, create `Candidate` rows

---

## Django Model Mapping

### Election
```python
Election.objects.update_or_create(
    source_id=election["id"],
    defaults={
        "name": election["name"],
        "election_date": election["electionDay"],
        "jurisdiction_level": parse_jurisdiction(election["ocdDivisionId"]),
        "state": parse_state(election["ocdDivisionId"]),
        "source": "civic_api",
    }
)
```

### Race (from contest)
```python
Race.objects.update_or_create(
    election=election_obj,
    office_title=contest.get("office") or contest.get("referendumTitle"),
    jurisdiction=contest["district"]["name"],
    defaults={
        "race_type": "measure" if contest["type"] == "Referendum" else "candidate",
        "geography_scope": contest["district"].get("scope", ""),
        "source": "civic_api",
        "certification_status": "upcoming",
    }
)
```

### Candidate (from contest.candidates)
```python
for c in contest.get("candidates", []):
    Candidate.objects.update_or_create(
        race=race_obj,
        name=c["name"],
        defaults={"party": c.get("party", ""), "incumbent": False}
    )
```

---

## Celery Sync Task Pattern

The sync runs on a schedule (e.g. every 6 hours). Recommended structure:

```python
# tasks.py
from celery import shared_task
from .civic_client import CivicAPIClient

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_elections(self):
    client = CivicAPIClient()
    try:
        elections = client.list_elections()
        for election in elections:
            sync_election_races.delay(election["id"])
    except CivicAPIError as exc:
        raise self.retry(exc=exc)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_election_races(self, election_id):
    # Query voterinfo for a representative set of addresses
    # (one per state, or use known jurisdiction centroids)
    ...
```

---

## Error Handling

| HTTP Status | Meaning | Action |
|---|---|---|
| 400 | Bad address / no election | Log warning, skip — do not raise |
| 403 | Invalid API key | Raise immediately, alert ops |
| 404 | Election not found | Log, remove stale Election if needed |
| 429 | Rate limit | Retry with exponential backoff |
| 503 | API unavailable | Retry with backoff, Celery handles |

The Civic API returns `400` for valid addresses with no active contests — treat this as "no data" not an error.

---

## Address Resolution for ZIP/State Filters

When a user filters races by ZIP code:
1. Use the ZIP as the address string: `f"{zip_code} USA"`
2. Call `voterinfo` for each active election
3. Return all matching contests, deduplicating by `(office_title, jurisdiction, election_id)`

When filtering by state only, use the state capital address as a representative query, then supplement with statewide races from the stored database (scope = `statewide`).

---

## Environment & Configuration

```python
# settings.py
CIVIC_API_KEY = env("CIVIC_API_KEY")  # never hardcode
CIVIC_API_BASE = "https://www.googleapis.com/civicinfo/v2"
CIVIC_SYNC_INTERVAL_HOURS = 6
```

Store `CIVIC_API_KEY` in `.env` (local) and the production secrets manager. Never commit it.

---

## Caveats & Known Limitations

- **Coverage gaps**: The Civic API does not cover all local races. When `voterinfo` returns no contests for a location, prompt the user to use the local race wizard.
- **Address normalization**: The API is sensitive to address format. Always include city + state + ZIP for best results.
- **Referendum text**: `referendumText` can be very long. Truncate to 2000 chars for the `Race` model display field; store full text separately if needed.
- **Candidate photos/bios**: Not provided by the Civic API. Source from candidate website links when available in the response.
- **`electionId` required**: `voterinfo` requires a specific `electionId`. You must call `/elections` first to get valid IDs.
