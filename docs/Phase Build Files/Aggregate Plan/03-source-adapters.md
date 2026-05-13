# Source Adapters — Per-Source Specifications

> **Status: ✅ IMPLEMENTED** — All Tier 1 and Tier 2 adapters built and tested (FEC ✅, Congress ✅, Open States ✅, Census ✅, OpenElections ✅). MEDSL deferred to post-election manual trigger.

Each adapter lives under `backend/integrations/<source>/` and follows the same internal structure as the existing `integrations/civic/` module. Adapters **never write directly to core models**. They fetch raw data, normalize it into an intermediate dict, and pass it to the orchestrator layer (see [04-orchestration.md](04-orchestration.md)).

---

## Adapter Interface Convention

```python
# Every adapter exposes these in tasks.py:

@shared_task(bind=True, max_retries=3)
def sync_<source>_<entity>(self, **scope_kwargs):
    """
    Fetch raw records from source.
    Map to intermediate dicts via mappers.
    Pass to orchestrator for matching and upsert.
    Log to SyncLog.
    """
```

```python
# Every adapter's mappers.py exposes:

def map_<entity>(raw: dict) -> dict:
    """
    Convert source-specific raw payload to a normalized intermediate dict.
    Keys map to CivicMirror model fields or orchestrator input contracts.
    Returns None to signal 'skip this record'.
    """
```

---

## Adapter 1: `integrations/fec/`

### Purpose
Enrich federal candidate and election cycle data from the OpenFEC API.

### API Details
- **Base URL:** `https://api.open.fec.gov/v1/`
- **Key endpoints:**
  - `/candidates/` — candidate listing by office, state, election year
  - `/candidates/{candidate_id}/` — individual candidate detail
  - `/elections/` — election summaries by office/cycle
- **Authentication:** `?api_key=<FEC_API_KEY>` query param
- **Rate limits:** 1,000 requests/hour per key (free tier); use page-size 100, respect `X-RateLimit-Remaining` header
- **API Key:** Already in project (see `docs/Secrets/API-Keys.md`)

### Key Field Mappings

| FEC field | CivicMirror target |
|---|---|
| `candidate_id` | `Candidate.fec_candidate_id` |
| `name` | Cross-reference; do NOT overwrite `Candidate.name` from Civic |
| `office_full` | Used for race matching via `Race.normalized_office_title` |
| `state` | `Election.state` |
| `district` | `Race.ocd_division_id` construction |
| `party_full` | Enrich `Candidate.party` if blank |
| `incumbent_challenge_full` | Set `Candidate.incumbent` if not already set |
| `election_years` | `ElectionCycle.cycle_year` matching |

### Scope of new Race creation
- FEC does **not** create new `Race` records if a Civic-sourced race exists for the same office/district/cycle.
- A FEC-only `Race` stub may be created **only** for federal races where Civic has no data and the cycle is current/upcoming. These are created with `match_confidence = 'medium'` and flagged for review.

### Implementation Tasks
1. `integrations/fec/client.py` — paginated GET with `X-RateLimit-Remaining` handling
2. `integrations/fec/mappers.py` — map candidate and election payloads to intermediate dicts
3. `integrations/fec/tasks.py` — `sync_fec_candidates(cycle_year)` Celery task

---

## Adapter 2: `integrations/congress/`

### Purpose
Enrich federal incumbents with biographical data, contact information, and cross-reference IDs from `unitedstates/congress-legislators`.

### Data Source Details
- **Files (GitHub raw):**
  - `https://theunitedstates.io/congress-legislators/legislators-current.json`
  - `https://theunitedstates.io/congress-legislators/legislators-historical.json`
- **Format:** JSON array
- **Authentication:** None required (public GitHub raw)
- **Update cadence:** Community-maintained; weekly pull is sufficient
- **API Key:** None needed

### Key Field Mappings

| congress-legislators field | CivicMirror target |
|---|---|
| `id.bioguide` | `Candidate.bioguide_id` |
| `id.fec` (list) | Cross-reference with `fec_candidate_id` |
| `name.official_full` | Stored in `source_metadata['congress']['official_full']`; not overwriting `Candidate.name` |
| `terms[-1].type` (rep/sen) | Race type confirmation |
| `terms[-1].state` | Match to `Election.state` |
| `terms[-1].district` | Match to `Race.ocd_division_id` |
| `contact_form`, `phone`, `office` | `Candidate.contact_phone`, `Candidate.contact_office` |
| `social.twitter`, `social.facebook`, `social.youtube` | `Candidate.source_metadata['congress']` |

### Matching Strategy
1. If `Candidate.bioguide_id` already set → update existing record
2. Else: try FEC ID cross-reference (match by `fec_candidate_id`)
3. Else: try normalized name + state + office type + current term district

### Implementation Tasks
1. `integrations/congress/client.py` — download JSON files with ETag caching
2. `integrations/congress/mappers.py` — map legislator entries to enrichment dicts
3. `integrations/congress/tasks.py` — `sync_congress_legislators()` weekly Celery task

---

## Adapter 3: `integrations/openstates/`

### Purpose
Enrich state-level incumbents with biographical data, chamber, district, and contact info from the Open States API.

### API Details
- **Base URL:** `https://v3.openstates.org/`
- **Key endpoint:** `/people` with `jurisdiction=ocd-division/country:us/state:<xx>`
- **Authentication:** `?apikey=<OPENSTATES_API_KEY>` query param
- **Rate limits:** 500 requests/day on free tier; paginate with `page` and `per_page=50`
- **API Key:** Already in project (see `docs/Secrets/API-Keys.md`)

### Key Field Mappings

| Open States field | CivicMirror target |
|---|---|
| `id` (OCD person ID) | `Candidate.openstates_person_id` |
| `name` | Cross-reference; not overwriting Civic name |
| `party` | Enrich if blank |
| `current_role.chamber` | Race/office matching |
| `current_role.district` | Race OCD ID matching |
| `current_role.jurisdiction` | `Election.state` matching |
| `image` | `Candidate.image_url` if blank |
| `email`, `links` | `Candidate.source_metadata['openstates']` |

### Matching Strategy
1. Match by `openstates_person_id` if already set
2. Else: normalized name + state + chamber + district

### Important Limitation
Open States covers **current officeholders**, not all candidates. Do not create new `Candidate` records from Open States for candidates not already in the system.

### Implementation Tasks
1. `integrations/openstates/client.py` — paginated GET per state with rate-limit guard
2. `integrations/openstates/mappers.py` — map person records to enrichment dicts
3. `integrations/openstates/tasks.py` — `sync_openstates_legislators(state)` per-state Celery task

---

## Adapter 4: `integrations/census/`

### Purpose
Resolve addresses and ZIP codes to district identifiers and OCD division IDs. This is a **foundational pre-pass** that other adapters depend on for cross-source matching.

### Data Sources
- **Census Geocoder API:** `https://geocoding.geo.census.gov/geocoder/`
  - No API key required
  - Benchmark: `Public_AR_Current`
  - Returns: state, county, tract, congressional district, state leg district
- **OCD Division IDs:** `https://github.com/opencivicdata/ocd-division-ids`
  - Download `identifiers/country-us.csv` as static reference file
  - No API key required

### Key Outputs
1. `resolve_address(address: str) → DistrictRecord[]` — returns matched districts for an address
2. `resolve_zip(zip_code: str) → DistrictRecord[]` — returns approximate districts for a ZIP (multi-district ZIPs flagged as approximate)
3. OCD ID construction from state + district type + district number

### ZIP-Level Caveat
ZIP codes can span multiple congressional or legislative districts. Any district resolved from ZIP alone must be:
- Marked as `approximate=True` in the resolution result
- Not used as a hard match key in the orchestrator

### Implementation Tasks
1. `integrations/census/client.py` — Census Geocoder REST client (no key needed)
2. `integrations/census/ocd_loader.py` — load and index OCD division CSV
3. `integrations/census/resolver.py` — `resolve_address`, `resolve_zip` public functions
4. `integrations/census/models.py` — `DistrictRecord` model (staging table)
5. `integrations/census/tasks.py` — `refresh_district_records()` scheduled task

---

## Adapter 5: `results/adapters/openelections/`

### Purpose
Ingest historical certified election results from the OpenElections project (CSV files per state per year, hosted on GitHub).

### Data Source Details
- **GitHub org:** `https://github.com/openelections`
- **Per-state repos:** e.g., `openelections-data-ca`, `openelections-data-ny`
- **File format:** CSV per election event
- **Columns (standard):** `county`, `precinct`, `office`, `district`, `party`, `candidate`, `votes`, `winner`
- **Authentication:** None (public GitHub); use GitHub API or raw download URLs
- **Update cadence:** Post-election; new files added weeks to months after election day

### Design Considerations
- This adapter writes to a `Result` model (existing `results` app), not to `Race` or `Candidate` directly
- New `Race` records may be created for historical elections not covered by Civic, with `source='openelections'`
- Uses `canonical_key` construction for deduplication matching against existing races

### Implementation Tasks
1. `results/adapters/openelections/client.py` — GitHub API client, per-state repo discovery
2. `results/adapters/openelections/mappers.py` — CSV row to intermediate result dict
3. `results/adapters/openelections/tasks.py` — `ingest_openelections_state(state, election_year)` Celery task (admin-triggered or scheduled weekly check for new files)

---

## Adapter 6: `results/adapters/medsl/`

### Purpose
Ingest MIT Election Data and Science Lab (MEDSL) historical returns from Harvard Dataverse as supplemental/validation data for historical result backfill.

### Data Source Details
- **URL:** `https://electionlab.mit.edu/data` → Harvard Dataverse
- **Format:** CSV bulk download
- **Coverage:** Federal (House, Senate, President) and some state races
- **Authentication:** None (public Dataverse API)
- **Update cadence:** Post-election, bulk annual releases

### Design Considerations
- Use as secondary/validation source after OpenElections
- Same `results` domain write path as OpenElections
- Useful for: validation against OpenElections data, filling coverage gaps for states not in OpenElections

### Implementation Tasks
1. `results/adapters/medsl/client.py` — Dataverse API / direct download client
2. `results/adapters/medsl/mappers.py` — CSV to intermediate dict
3. `results/adapters/medsl/tasks.py` — `ingest_medsl_results(dataset_id)` Celery task

---

## Summary: What Each Adapter Touches

| Adapter | Creates Election? | Creates Race? | Creates Candidate? | Enriches Candidate? | Creates Result? |
|---|---|---|---|---|---|
| civic (existing) | Yes (primary) | Yes (primary) | Yes (primary) | — | No |
| fec | Supplemental only | Supplemental only | No (enriches) | Yes | No |
| congress | No | No | No | Yes | No |
| openstates | No | No | No | Yes (incumbents only) | No |
| census | No | No | No | No | No (district data only) |
| openelections | Historical only | Historical only | Historical only | No | Yes |
| medsl | Historical only | Historical only | Historical only | No | Yes |

---

## Next Document

[04-orchestration.md](04-orchestration.md) — Shared matcher and enrichment-merger services.
