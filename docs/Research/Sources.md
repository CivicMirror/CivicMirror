# Election Data Sources Research

This document catalogs promising election-data sources and reference projects for CivicMirror.

## Goal

CivicMirror needs a realistic mix of sources that can help mirror real-world elections for:

- election metadata and calendars
- ballot races and measures
- candidate and office information
- district and jurisdiction mapping
- official results

The target is **free** or **very low cost** sources wherever possible, with data that is:

- programmatically available (API, JSON, CSV, XML, bulk download)
- refreshable on a schedule
- stageable in a local cache/database for fast page loads
- practical for normalizing into CivicMirror models

Google Civic API and OpenFEC are already available to this project and should be treated as baseline sources.

---

## Full Source Catalog

| Source | Coverage | Access | Cost | Update cadence | Best use in CivicMirror | Main limitations |
|---|---|---|---|---|---|---|
| Google Civic Information API | Federal + many state/local upcoming elections | REST JSON | Free | Election-cycle / near-live | Primary live ballot, contest, candidate, measure, polling-location source | Incomplete local coverage; no historical results |
| OpenFEC API | Federal only | REST JSON | Free | Filing-driven / frequent | Federal candidate metadata and election summaries | No local/state data; no ballot text; no official results |
| OpenElections | Historical federal/state/local results | CSV + GitHub repos | Free | Post-election | Certified results staging and state adapter patterns | Historical only; uneven local coverage |
| MEDSL / Harvard Dataverse | Historical official returns | CSV bulk | Free | Post-election batch | Federal and local historical result backfill | No live/current ballot data |
| United States Congress Legislators | Federal officeholder metadata | JSON/CSV/YAML | Free | Ongoing community updates | Federal incumbent enrichment, crosswalk IDs, contact data | Mostly incumbents/officeholders, not all challengers |
| Open States API | State legislators / jurisdictions | REST JSON + bulk dump | Free tier | Frequent | State incumbent enrichment and jurisdiction metadata | Not a primary election-race source |
| U.S. Census Geocoder + TIGER/Line | National geography and districts | REST + bulk shapefiles | Free | Annual / periodic | ZIP/address to district mapping and boundary staging | No race or ballot data |
| Open Civic Data division IDs | National jurisdiction identifiers | CSV | Free | Static reference | Standard identifier layer for race normalization | Identifier reference only |
| Voting Information Project (VIP) spec / state VIP feeds | Election/ballot schema, some direct feeds | XML/CSV | Free | Election-cycle | Schema alignment and direct-state ingestion when available | No single public national VIP feed |
| `openelections/clarify` | Official-results parsing helper | Python library | Free | Library/project | Parsing Clarity-hosted election-night results | Not a data source by itself |
| FEC election dates pages/files | Federal election schedule | Excel/PDF/web pages | Free | Election-cycle | Supplemental federal calendar validation | No API; federal only |
| WeVoteServer | Reference project | Open-source repo | Free | N/A | Source-ingestion patterns and multi-source architecture ideas | Not a direct source |
| MinnPost election-night-api | Reference project | Open-source repo | Free | N/A | Official-results ingestion patterns | Older architecture; not a direct source |
| Ballotpedia API | Ballots, measures, candidates | API + site pages | Likely paid / partner access | Unknown | Strategic enrichment if access becomes available | No public low-cost access identified |
| Democracy Works Elections API | Broad election + voter info | REST JSON | Enterprise / above budget | Ongoing | Strategic one-stop source if budget changes | Over current cost target |

---

## Detailed Notes

### 1. Google Civic Information API

- **URL:** `https://www.googleapis.com/civicinfo/v2`
- **Coverage:** Upcoming federal elections plus many state and local races, ballot measures, polling places, early voting, and election administration contacts.
- **Access:** REST JSON via `/elections` and `/voterinfo`
- **Cost:** Free with API key
- **Best fit:** **Primary live election feed**
- **Useful fields:**
  - election IDs and election dates
  - contests / offices / district scope
  - candidate names, parties, URLs, photos, channels
  - referendum titles and text
  - polling locations, drop-off sites, early-vote sites
  - OCD division IDs
- **Limitations:**
  - requires address + electionId for detailed ballot data
  - local coverage varies by state participation
  - does not provide historical results

**Recommendation:** Keep as **Tier 1** source for current/upcoming ballots and election administration data.

---

### 2. OpenFEC API

- **URL:** `https://api.open.fec.gov/v1/`
- **Docs:** `https://api.open.fec.gov/developers/`
- **Coverage:** Federal candidates and election-cycle data
- **Access:** REST JSON
- **Cost:** Free
- **Best fit:** **Federal candidate enrichment**
- **Useful fields:**
  - candidate ID
  - office, office full name
  - state, district
  - party
  - incumbent/challenger/open-seat status
  - election years
  - committee/finance links for future use
- **Limitations:**
  - federal only
  - no ballot measure text
  - not an official results source

**Recommendation:** Keep as **Tier 1** source for federal candidate metadata and federal election supplementation.

---

### 3. OpenElections

- **URLs:**
  - `https://github.com/openelections`
  - `https://openelections.net`
- **Coverage:** Historical certified results across many states, with per-state repos
- **Access:** CSV / GitHub bulk download / reusable ingestion code
- **Cost:** Free
- **Best fit:** **Historical certified results + adapter patterns**
- **Useful fields:**
  - office
  - district
  - candidate
  - party
  - county / precinct
  - vote totals
- **Strengths:**
  - proven normalization approach
  - state-by-state loader pattern can inform CivicMirror adapters
  - good fit for post-election `OfficialResult` ingestion
- **Limitations:**
  - not a live pre-election ballot source
  - uneven local completeness by state

**Recommendation:** Make this **Tier 2** for official results and post-election backfill.

---

### 4. MEDSL / Harvard Dataverse Election Returns

- **URLs:**
  - `https://electionlab.mit.edu/data`
  - Harvard Dataverse MEDSL collections
- **Coverage:** Historical federal and many local/state official returns
- **Access:** CSV bulk download
- **Cost:** Free
- **Best fit:** **Historical result backfill and research-grade archives**
- **Useful fields:**
  - candidate
  - office
  - district
  - party
  - county / jurisdiction FIPS
  - vote totals
  - winner flags
- **Limitations:**
  - post-election only
  - not a live contest source
  - local depth depends on state reporting

**Recommendation:** Use as **Tier 2** for historical result population and validation against other result sources.

---

### 5. `unitedstates/congress-legislators`

- **URL:** `https://github.com/unitedstates/congress-legislators`
- **Coverage:** Current and historical members of Congress
- **Access:** JSON / CSV / YAML direct download
- **Cost:** Free
- **Best fit:** **Federal candidate and officeholder enrichment**
- **Useful fields:**
  - biographical data
  - current term and district
  - website, office address, phone
  - FEC IDs
  - Ballotpedia name cross-reference
  - social media handles
- **Limitations:**
  - strongest for incumbents and officeholders
  - does not cover every challenger

**Recommendation:** Use as **Tier 1 enrichment** for federal candidate records alongside OpenFEC.

---

### 6. Open States API

- **URL:** `https://v3.openstates.org/`
- **Docs:** `https://docs.openstates.org/api-v3/`
- **Coverage:** State legislators, jurisdictions, bills, chambers, committees
- **Access:** REST JSON and bulk data
- **Cost:** Free tier available
- **Best fit:** **State-level incumbent enrichment**
- **Useful fields:**
  - legislator name
  - party
  - chamber / district
  - contact details
  - official website
  - images
- **Limitations:**
  - not a direct election-race source
  - focused on officeholders, not all candidates

**Recommendation:** Use as **Tier 2 enrichment** where state incumbent details are needed.

---

### 7. U.S. Census Geocoder and TIGER/Line

- **URLs:**
  - `https://geocoding.geo.census.gov/`
  - `https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html`
- **Coverage:** National geography, districts, tabulation areas, counties, places
- **Access:** REST geocoder + bulk shapefiles
- **Cost:** Free
- **Best fit:** **District mapping and geographic normalization**
- **Useful fields / outputs:**
  - address to state/county/district resolution
  - FIPS codes
  - congressional district data
  - VTD / geography shapes for local staging
- **Limitations:**
  - no election/race payloads
  - geometry maintenance adds ingestion complexity

**Recommendation:** Make this **Tier 1 infrastructure source** for jurisdiction mapping and ZIP/address fallback logic.

---

### 8. Open Civic Data Division IDs

- **URL:** `https://github.com/opencivicdata/ocd-division-ids`
- **Coverage:** National jurisdiction and district identifier vocabulary
- **Access:** CSV/reference files
- **Cost:** Free
- **Best fit:** **Normalization standard**
- **Useful fields:**
  - jurisdiction IDs
  - names
  - hierarchy references
- **Limitations:** Not a live data feed

**Recommendation:** Use as a **reference layer** for normalizing `ocd_division_id` across all sources.

---

### 9. Voting Information Project (VIP)

- **URL:** `https://github.com/votinginfoproject/vip-specification`
- **Coverage:** Ballot, candidate, polling-place, and election-authority schema used by participating jurisdictions
- **Access:** XML / CSV spec, plus some direct state feeds when published
- **Cost:** Free
- **Best fit:** **Schema alignment and direct-state ingestion where available**
- **Useful data concepts:**
  - contests
  - candidates
  - polling places
  - street segments
  - election authorities
- **Limitations:**
  - no single public national aggregator feed outside Google Civic
  - direct state VIP usage varies

**Recommendation:** Treat VIP as a **data-model and interoperability guide**, plus an optional direct-source path for states that publish feeds openly.

---

### 10. `openelections/clarify`

- **URL:** `https://github.com/openelections/clarify`
- **Coverage:** Software parser for Clarity-hosted official results
- **Access:** Python library
- **Cost:** Free
- **Best fit:** **Future unofficial/live results parsing**
- **Why it matters:** Many jurisdictions publish election-night results through Clarity. This library may reduce custom parser work.
- **Limitations:** Not a source itself; only useful when a state/county site uses Clarity.

**Recommendation:** Keep as a **future implementation aid** for state results adapters.

---

### 11. FEC Election Dates Files

- **URL:** `https://www.fec.gov/introduction-campaign-finance/how-to-research-public-records/election-dates/`
- **Coverage:** Federal election schedule documents
- **Access:** Web pages, Excel, PDF
- **Cost:** Free
- **Best fit:** **Federal schedule cross-check**
- **Limitations:** No clean API; federal only

**Recommendation:** Use only as a **supplemental validation source** for federal election calendars.

---

### 12. Ballotpedia

- **Coverage:** Strong ballot measure, candidate, and race information
- **Access:** WeVoteServer shows Ballotpedia API-style endpoints and API-key usage, plus HTML scraping for supplemental data.
- **Cost:** No public low-cost tier identified
- **Best fit:** Strategic enrichment only if access becomes available
- **Important note:** Based on WeVoteServer, this appears to require a Ballotpedia API key and/or partner-style access, with additional page scraping for some assets.
- **Limitations:**
  - no public free/cheap plan identified during this research
  - should not be assumed available at current budget

**Recommendation:** Keep on the **watch list**, but do **not** plan core architecture around it.

---

### 13. Democracy Works Elections API

- **Coverage:** Very broad election, ballot, and voter-information coverage
- **Access:** REST JSON
- **Cost:** Enterprise / above current budget
- **Best fit:** Strategic long-term option if sponsorship or funding increases
- **Limitations:** Does not fit current low-cost target

**Recommendation:** Document as a **future premium option**, not part of the current plan.

---

## Open-Source Projects Worth Studying

These are not primary data feeds, but they are useful references for ingestion architecture.

### WeVoteServer

- **Repo:** `https://github.com/wevote/WeVoteServer`
- **Why it matters:** Shows a multi-source ingestion pattern with separate import controllers for Google Civic, Ballotpedia, Vote USA, CTCL, and representative-related data.
- **Useful lesson:** Source-specific import controllers feeding a shared normalization/batch system is a strong pattern for CivicMirror.

### MinnPost election-night-api

- **Repo:** `https://github.com/MinnPost/election-night-api`
- **Why it matters:** Useful reference for official-results ingestion and election-night data workflows.
- **Useful lesson:** Good model for results synchronization and staging architecture even if the project is older.

### WeVoteBase

- **Repo:** `https://github.com/adborden/WeVoteBase`
- **Why it matters:** Older project, but still useful for discovering historical source lists and prior integration ideas.

### `psalzman/mcp-openfec`

- **Repo:** `https://github.com/psalzman/mcp-openfec`
- **Why it matters:** Useful as a reference around OpenFEC data access and future finance-related features.

---

## Recommended Stack for CivicMirror

### Tier 1 — Core stack to build around now

1. **Google Civic Information API**
   - upcoming elections
   - live ballot races and measures
   - polling locations
   - election authorities

2. **OpenFEC API**
   - federal candidate metadata
   - federal election supplementation

3. **U.S. Census Geocoder + TIGER/Line**
   - address / ZIP to district resolution
   - geographic boundary staging

4. **Open Civic Data division IDs**
   - shared identifier normalization

5. **`unitedstates/congress-legislators`**
   - federal incumbent enrichment
   - FEC crosswalk IDs
   - website/contact info

### Tier 2 — Add next for depth and comparison

1. **OpenElections**
   - certified results
   - historical result backfill
   - state adapter patterns

2. **MEDSL**
   - long-range historical results archive
   - validation / backfill

3. **Open States**
   - state incumbent enrichment
   - jurisdiction context

4. **VIP direct-state feeds**
   - use opportunistically in states where public access exists

### Tier 3 — Future / strategic

1. **`openelections/clarify`**
   - faster path to live unofficial results in Clarity jurisdictions

2. **Ballotpedia**
   - only if access becomes feasible

3. **Democracy Works**
   - only if budget or sponsorship changes significantly

---

## Sources That Should Not Be Primary Dependencies

### ProPublica Congress API

- Formerly useful, but now discontinued / archived.
- Do not plan future ingestion work around it.

### OpenSecrets API

- Formerly useful, but now discontinued.
- Use OpenFEC instead for federal finance-adjacent data.

---

## Practical Ingestion Direction

The most realistic low-cost CivicMirror architecture is:

1. **Current/upcoming ballots:** Google Civic first
2. **Federal candidate enrichment:** OpenFEC + `congress-legislators`
3. **Geographic resolution:** Census + OCD IDs
4. **Official results and historical mirror:** OpenElections + MEDSL
5. **State incumbent enrichment:** Open States
6. **Optional direct-state adapters:** VIP feeds, Clarity parsers, official state portals where needed

This keeps the core system under the current budget target while still allowing future expansion into richer paid sources if the project grows.
