# Phase 7 Official Results Ingestion and Comparison

## Goal
Add official-results ingestion and side-by-side comparison so CivicMirror can show how mock voting tracked against certified election outcomes without assuming every state exposes data in the same format.

## Prerequisites
- Phase 1 Foundation complete
- Phase 2 Authentication complete
- Phase 3 Google Civic API ingestion complete
- Phase 4 Public Race Browser complete
- Phase 5 Mock Voting complete
- Phase 6 Local Race Submission Wizard complete

### Official-results complexity baseline
This phase depends on the Phase 1 schema spike being treated seriously.

Official results are not always a simple one-row-per-candidate feed. The design must account for:
- multi-seat races with multiple winners
- ranked-choice tallies with round-by-round data
- write-in aggregates that may not map to a named candidate row
- precinct or county splits that may exist in some state feeds
- unofficial election-night counts versus certified final counts

Launch posture:
- support the core comparison view for straightforward races
- preserve extra state-specific detail in raw payloads rather than discarding it
- mark races as partial when mapping is incomplete instead of pretending certainty

### OfficialResult model
Implement or finalize `OfficialResult` with fields:
- `race` (FK)
- `candidate` (FK, nullable for write-ins or unmapped rows)
- `measure_option` (FK, nullable)
- `vote_count`
- `vote_pct`
- `is_winner` (bool)
- `result_type` (`official`, `unofficial`)
- `certified_at` (nullable)
- `source_url`
- `raw_payload` (JSON for state-specific extras)

Recommended supporting fields for smoother ingestion:
- `round_number` (nullable, for ranked-choice detail)
- `jurisdiction_fragment` (nullable, for county/precinct splits)
- `is_write_in_aggregate` (bool)

### State adapter architecture
Create an abstract adapter layer rather than hard-coding one state feed format into the core task.

Base class:
- `StateResultsAdapter`
- required method: `fetch_results(election_date, state)`

Adapter responsibilities:
- fetch upstream data
- normalize rows into CivicMirror's result DTOs
- preserve upstream raw details in `raw_payload`
- classify whether the result is official or unofficial
- report whether mapping confidence is full or partial

### Adapter registry and app wiring
- Maintain an adapter registry mapping state abbreviation → adapter class.
- Register the mapping during Django app startup in `AppConfig`.
- Keep the registry discoverable and testable; avoid hidden import side effects spread across modules.

Example structure:
- `results/adapters/base.py`
- `results/adapters/registry.py`
- `results/adapters/ma.py`
- `results/adapters/co.py`
- `results/adapters/ca.py`

### Initial target states
Start with 2-3 states that have relatively accessible election result feeds and give the team useful coverage diversity.

Recommended launch candidates:
- Massachusetts
  - manageable scope and commonly available municipal/state result publishing patterns
- Colorado
  - strong digital election-data practices and useful statewide feed coverage
- California
  - high-volume, structurally diverse data that stress-tests adapter flexibility

Document why each state was selected and what feed quality limitations remain.

### Official results ingestion task
Create a Celery task:
- `ingest_official_results(state, election_id)`

Task behavior:
- runs after election day for supported states
- retries until results are available or a configured cutoff is reached
- records whether results are unofficial or certified
- upserts `OfficialResult` rows idempotently
- logs mapping failures and partial matches for operator review

Recommended flow:
1. locate the `Election` and relevant `Race` rows
2. load the correct adapter from the registry
3. fetch normalized results
4. match normalized rows to candidates/measure options
5. write `OfficialResult` rows
6. update race/election certification statuses where appropriate

### Certification status transitions
Use `Race.certification_status` consistently across the app:
- `upcoming`
- `results_pending`
- `results_certified`
- `partial_results`

Transition rules:
- after voting closes, races move from `upcoming` to `results_pending`
- once official certified data is ingested cleanly, move to `results_certified`
- if official data is only partially mappable, use `partial_results`

Do not mark races certified based only on unofficial election-night numbers.

### Long-term result status model
The current launch model can keep `Race.certification_status` and per-row `OfficialResult.result_type` because those fields already support the immediate UI distinction between unofficial and certified results.

For a cleaner long-term model, split the concepts that are currently blended into `certification_status`:

```ts
type ResultAvailability = 'none' | 'available';
type ResultCertification = 'unofficial' | 'certified';
type ResultCompleteness = 'unknown' | 'partial' | 'complete';
type ResultSourceAuthority = 'election_office' | 'community' | 'third_party';
```

Recommended future fields:
- `Race.result_availability` — whether any election result rows are available.
- `Race.result_certification` — whether the available source result set is unofficial or certified.
- `Race.result_completeness` — whether the available rows fully cover the race and map cleanly.
- `Race.result_source_authority` — whether the data came from an election office, community entry, or third-party feed.
- `OfficialResult.result_type` — keep this per row so mixed or corrected imports can be audited.

Recommended migration path:
1. Keep the current `certification_status` values for compatibility.
2. Add derived helper functions in the API/frontend that calculate the new conceptual fields from `certification_status` and `OfficialResult.result_type`.
3. Once adapters are stable, add explicit database fields for availability, certification, completeness, and source authority.
4. Treat `results_certified` as a display state derived from `result_certification === 'certified'` and `result_completeness === 'complete'`.
5. Treat `partial_results` as a completeness state, not as a certification state.

Suggested display mapping:
- `availability = none` → Results Pending
- `availability = available`, `certification = unofficial` → Unofficial Results
- `availability = available`, `certification = certified`, `completeness = complete` → Certified Results
- `availability = available`, `completeness = partial` → Partial Results, with unofficial/certified source detail still visible

This split avoids confusing phrases such as "official unofficial results" and makes it possible to show results from election-office feeds before certification without implying finality.

### Race archival after results
Once a race's official results have been processed or the race has closed without results:
- set `race_status = archived` to close voting and mark the race as final
- archived races remain fully viewable in the public browser and comparison UI — they are never deleted
- mock tally and official-results comparison views remain accessible indefinitely
- admin retains the ability to reopen an archived race and update official results if corrections are needed

### Candidate and option matching strategy
Matching official rows back to CivicMirror race entities will be imperfect.

Recommended matching order:
1. exact normalized candidate/option name match
2. known alias mapping per adapter when states abbreviate or format names differently
3. write-in aggregate fallback to a null candidate row with `is_write_in_aggregate = true`
4. mark as partial if a confident mapping cannot be made

For measure races:
- map state-specific response values like `For/Against` or `Approve/Reject` into `Yes/No` `MeasureOption` rows via adapter-level normalization

### Comparison UI on race detail
Add an official-results comparison section to the race detail page.

Display:
- mock tally and election results side by side
- counts and percentages for each candidate/option
- status label showing whether available numbers are unofficial, certified, partial, or pending
- source attribution link from `source_url`

UI options:
- MUI table for precise numeric comparison
- grouped bar chart when there are only a few candidates/options

### Status badge updates across the app
- Reuse the certification state on list cards and detail headers.
- When a race reaches `results_certified`, update all status chips and summary text accordingly.
- Keep unofficial results visually distinct from certified results.

### Unsupported mappings and partial results
When official results do not cleanly map to CivicMirror's schema:
- keep ingested raw data in `raw_payload`
- set the race to `partial_results`
- show a user-facing note that the official comparison is incomplete
- surface the issue in admin/ops reporting for follow-up adapter improvements

## Deliverables Checklist
- [ ] Official-results schema supports winners, unofficial vs official states, write-ins, and raw state-specific payloads
- [ ] `StateResultsAdapter` base class created with a `fetch_results(election_date, state)` contract
- [ ] Adapter registry maps state abbreviations to concrete adapter classes in Django app startup
- [ ] Initial adapters implemented for 2-3 target states with documented feed assumptions
- [ ] Celery task `ingest_official_results(state, election_id)` ingests and upserts official result rows
- [ ] Race certification status transitions follow upcoming → results_pending → results_certified or partial_results
- [ ] Candidate/measure-option matching strategy handles aliases, write-ins, and unmapped rows safely
- [ ] Race detail page shows mock tally vs election results side by side
- [ ] Race detail page clearly labels unofficial results separately from certified final results
- [ ] Status badges across list/detail views reflect certified vs pending vs partial official-result states
- [ ] Unsupported mappings surface as `partial_results` instead of misleadingly complete data
