# Architecture Overview — Multi-Source Aggregation

> **Status: ✅ IMPLEMENTED** — All adapters built. See `backend/integrations/` for the delivered code.

## Goal

CivicMirror needs a unified election data pipeline that ingests from multiple free/low-cost sources, stages data locally for fast page loads, and presents a consistent, deduplicated view of real-world elections.

The design must support:
- Multiple sources producing race/candidate records for the same real-world contest
- Safe enrichment (later sources add detail, they do not blindly overwrite primary data)
- Traceable provenance (every record knows which source(s) it came from)
- Incremental sync without full re-import on every run

---

## Reference: WeVoteServer Pattern

WeVoteServer uses source-specific import controllers, each feeding a shared batch/normalization layer:

```
import_export_google_civic/controllers.py
import_export_ballotpedia/controllers.py
import_export_ctcl/controllers.py
      ↓ all call ↓
import_export_batches/models.py  ← shared normalization + dedup
```

CivicMirror adapts this pattern to its existing Django/Celery stack:

```
integrations/<source>/
      ↓ raw fetch + map ↓
integrations/orchestrator/
      ↓ match + enrich + write ↓
elections models / results models
```

---

## Proposed Directory Structure

```
backend/
  integrations/
    civic/          ← EXISTING — Google Civic API client, tasks, mappers, cache
    fec/            ← NEW — OpenFEC federal candidate/election sync
    congress/       ← NEW — unitedstates/congress-legislators JSON sync
    openstates/     ← NEW — Open States state legislator enrichment
    census/         ← NEW — U.S. Census Geocoder + TIGER district resolution
    orchestrator/   ← NEW — RaceMatcher, CandidateMatcher, EnrichmentMerger
  results/
    adapters/
      openelections/ ← NEW — historical certified results (CSV + GitHub)
      medsl/         ← NEW — MEDSL/Harvard Dataverse historical returns
```

Each new source adapter follows the same internal structure:

```
integrations/<source>/
  __init__.py
  client.py      ← HTTP client with retry/backoff (same pattern as civic/client.py)
  mappers.py     ← Normalizes raw payload → intermediate dict (not direct model writes)
  tasks.py       ← Celery tasks that call orchestrator services, log to SyncLog
```

---

## Two Distinct Identity Concerns

A critical design rule: **source record identity** and **canonical race identity** are separate concepts.

### Source Record Identity

> "This is a raw record from FEC for candidate `H4CA05123` in the 2024 cycle."

Stored in: `SourceRecord` model (see [02-data-model.md](02-data-model.md))
Key: `(source, external_id)`

### Canonical Race Identity

> "This is the U.S. House CA-05 general election race in the November 2024 election."

Key: `(office_type, district_ocd_id, election_cycle_or_date, race_subtype)`
**Does not include `source`.** All sources that match this canonical identity enrich the same `Race` record.

This separation is what allows FEC candidates to be linked to a Civic-created race without duplicating it.

---

## Source Priority and Roles

| Source | Role | Creates new Race records? | Enriches existing Candidate? | Updates Election? |
|---|---|---|---|---|
| Google Civic API | Primary ballot source | Yes | Yes (primary) | Yes (primary) |
| OpenFEC API | Federal enrichment | Only if no Civic race found | Yes (enrichment) | Supplemental |
| congress-legislators | Federal enrichment | No | Yes (enrichment) | No |
| Open States | State enrichment | No | Yes (enrichment) | No |
| Census/OCD | District normalization | No | No | No |
| OpenElections | Historical results | Only for historical cycles | No | Status update only |
| MEDSL | Historical results | Only for historical cycles | No | Status update only |

**Key rule:** Civic is the authoritative source for active/upcoming races. FEC, congress-legislators, and OpenStates are enrichment-only for those records. Only OpenElections/MEDSL can create new `Race` records, and only for past election cycles not covered by Civic.

---

## Data Flow: Live Ballot Requests

```
User requests location (scope: federal|state|local, state: XX)
        ↓
  DB: Race.public_objects.filter(scope, state, last_synced_at fresh?)
        ↓ cache hit
  Return races to frontend
        ↓ cache miss or stale
  Trigger: sync_elections (Civic) → sync_election_races (Civic) [existing tasks]
        ↓ Civic returns races
  orchestrator.RaceMatcher: match raw races → canonical Race records (upsert)
        ↓
  orchestrator.CandidateMatcher: match raw candidates → Candidate records (upsert)
        ↓
  orchestrator.EnrichmentMerger: apply FEC/congress/OpenStates enrichment if available
        ↓
  Return races to frontend
        ↓ Civic returns no federal races for scope
  Fallback note added to response: "Federal candidate data from FEC (supplemental)"
  Background: enqueue fec_enrich_federal_races for this scope
```

Note: FEC is **not** a synchronous fallback on user requests. It is a background enrichment that runs nightly and on a post-sync hook. If Civic has no live data for a federal scope, the response can indicate "No verified ballot data; FEC candidate listing available" rather than synthesizing a live ballot from FEC.

---

## Data Flow: Background Enrichment (Scheduled)

```
Nightly:
  sync_fec_candidates(election_year=current)
    → FEC API: candidates by office/state/election_year
    → orchestrator.CandidateMatcher: link to existing Race+Candidate records
    → store FEC IDs in Candidate.fec_candidate_id / source_metadata

Weekly:
  sync_congress_legislators()
    → GitHub raw: legislators-current.json
    → orchestrator.CandidateMatcher: enrich incumbents with bioguide, contact, social
    → store in Candidate.source_metadata['congress']

Nightly:
  sync_openstates_legislators(state=each_state)
    → Open States API: /people?jurisdiction=ocd-division/country:us/state:<XX>
    → orchestrator.CandidateMatcher: link state incumbents to Candidate records
    → enrich with OpenStates person ID, chamber, contact

Weekly check / Post-election:
  check_openelections_new_results()
    → OpenElections GitHub: scan for new CSV drops
    → results/adapters/openelections/: ingest, stage, update election status
```

---

## OCD District Resolution: Foundational Pre-Pass

District/jurisdiction identity is the common fabric linking all sources. It must be resolved **before** enrichment tasks can reliably match records across sources.

The `census/` adapter will provide:
1. `resolve_address_to_districts(address)` → state + county + congressional district + OCD IDs
2. `resolve_zip_to_districts(zip_code)` → approximate districts (multi-district ZIPs flagged)
3. Cached district→OCD lookups staged in a `DistrictRecord` model

The orchestrator's match functions use OCD IDs as the first match tier. Name-based fallback is used only when OCD IDs are unavailable, and such matches are flagged with a lower confidence level.

---

## Confidence and Provenance

Every matched record carries provenance metadata. The plan calls for:

- `Race.source_metadata` (JSONField) — per-source reference IDs and sync timestamps
- `Candidate.source_metadata` (JSONField) — FEC ID, bioguide ID, OpenStates person ID
- `SourceRecord` model — raw payload store for replay and audit
- `RaceMatchLog` model or flag — confidence score, match tier, and flagged-for-review status

Low-confidence matches (name-only, no OCD ID) are flagged for admin review rather than auto-merged.

---

## What This Plan Does NOT Change

- The existing Google Civic integration (`integrations/civic/`) is kept as-is
- `Race.source = 'civic_api'` remains the primary race origin field
- The community submission flow (`LocalRaceSubmissionAPIView`) is unaffected
- The frontend location filter and API endpoint contract is not changed by this plan

---

## Next Document

[02-data-model.md](02-data-model.md) — Model additions and changes required.
