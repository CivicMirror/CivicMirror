# Phase 4 Public Race Browser

## Goal
Turn imported election data into a public browsing experience so anyone can discover races, inspect candidates or ballot measures, and understand current mock participation without needing an account.

## Prerequisites
- Phase 1 Foundation complete
- Phase 2 Authentication complete
- Phase 3 Google Civic API ingestion complete

### Race list API contract
Create a public `GET /api/races/` endpoint with filter params:
- `scope` (`national`, `state`, `zip`, `address`)
- `state`
- `zip`
- `address`
- `election_id`
- `certification_status`

Behavior rules:
- browsing is public; no auth required
- default to current/upcoming elections if `election_id` is omitted
- reject ambiguous filter combinations with a clear 400 response
- paginate results consistently with global DRF settings

### Address and ZIP race resolution
Race discovery must respect the Civic API's address dependency.

Resolution rules:
- `scope=address`
  - call `CivicAPIClient.get_voter_info(address, election_id)` on demand
  - import or refresh discovered races idempotently before returning results
- `scope=zip`
  - convert ZIP into a representative lookup address for that ZIP before calling `get_voter_info()`
  - clearly treat ZIP lookups as approximate coverage because Google Civic is address-based, not ZIP-based
- `scope=state`
  - use stored races where `geography_scope = statewide` and `Election.state` matches
- `scope=national`
  - return federal-scope races such as presidential, senate, and house contests tagged as national/federal

Implementation note:
- the address/ZIP lookup path should never store the raw address permanently in PostgreSQL
- import jobs triggered by public lookup should use the same canonical dedup logic from Phase 3

### Caching for Civic lookups
Phase 4 consumes the two-layer caching strategy established in Phase 3. Do not re-implement it here — call the shared resolution service.

**Layer 1 — Redis (1 hr hot dedup):**
- Cache key: `hash(normalized_address + election_id)`
- Prevents duplicate Civic API hits for the same address within the hour
- Cache both successful and empty-result lookups (empty results cached briefly at 5 min to avoid thundering herd)
- Hash the address rather than storing the raw string in the cache key

**Layer 2 — DB staleness (dynamic TTL):**
- Before hitting the Civic API, check `Election.last_synced_at` against the dynamic TTL for that election's date:
  - > 30 days out → 48 hrs
  - 7–30 days out → 24 hrs
  - 1–7 days out → 6 hrs
  - Election day → 1 hr
- If fresh: serve races from DB directly (no API call)
- If stale or never seeded: hit Civic API, persist new/updated races, update `last_synced_at`

Phase 4's address resolution endpoint is responsible only for invoking this check — the TTL logic lives in `integrations.civic` so it is reused by both on-demand queries and the scheduled Celery sync.

### Race serializer contract
Build a public serializer that includes enough data for race cards without making the frontend orchestrate multiple calls.

Include:
- election name
- office title
- jurisdiction
- race type
- candidate list with:
  - name
  - party
- measure summary for ballot measures
- `mock_vote_count` via queryset annotation
- `certification_status`
- source badge value (`civic_api` or `community`)
- status display value computed from dates and certification state

Recommended extra fields:
- `race_status`
- `voting_opens`
- `voting_closes`
- `viewer_has_voted` only when authenticated and only if it can be done cheaply

### Race detail API
Create `GET /api/races/{id}/` for full public detail.

Detail response should include:
- election metadata
- full candidate detail or measure options
- race status
- source attribution
- voting window
- current mock tally summary
- community moderation state only if relevant and public-safe

Do not expose internal moderation notes or submitter-private data in the public response.

### Status display logic
Normalize race status for the frontend into a simple, consistent display model:
- `upcoming`
  - current time is before `voting_opens`
- `results-pending`
  - voting window has closed and certified results are not available yet
- `results-certified`
  - `certification_status = results_certified`

Optional internal states may exist, but the public browser should not have a confusing explosion of labels.

### Query performance expectations
- Use `select_related('election')` for race list/detail queries.
- Use `prefetch_related('candidate_set', 'measureoption_set')` where appropriate.
- Annotate `mock_vote_count` instead of counting votes in Python.
- Filter out community races unless `community_status = active`.
- Exclude `race_status` values such as `pending_review`, `cancelled`, and `archived` from public list results.

### Frontend home page
Build a public home page focused on discovery using **progressive location disclosure** — the page is always useful, and becomes more relevant as the user optionally provides their location.

**Default state (no location known):**
- Show a national "What's Active Now" feed — all races currently in their voting window, sorted by mock vote count descending
- This is always populated because the Phase 3 sync seeds races from all 50 state capitals + DC
- A soft, non-blocking location prompt bar sits below the header: "📍 See races near you — [Enter ZIP or address →]"

**IP geolocation auto-detection:**
- On page load, silently call a free IP geolocation service (e.g. `ipapi.co/json`) to detect the user's state
- If detected with reasonable confidence, shift the feed to statewide races for that state
- Show a dismissible chip: "Showing races in **Massachusetts** · [Change]"
- Never block on this — fall back to national feed if geolocation fails or is slow

**Location tiers (each improves relevance):**

| Tier | Source | Feed shown |
|------|--------|------------|
| None | — | National active races, sorted by vote count |
| State auto-detected | IP geolocation | Statewide races for detected state |
| State manual | Dropdown | Statewide races for chosen state |
| ZIP | User input | Statewide + local races for that ZIP area |
| Address | User input | Full Civic API result for that address |

**Persistent location memory:**
- Store chosen location preference in `localStorage` (not server-side — address is ephemeral)
- Restore on return visits with a "Showing races near [ZIP]  · [Change]" chip

Required UI pieces:
- filter bar with tabs: National / State / ZIP / Address
- IP geolocation chip (auto-detected state, dismissible)
- election selector if more than one active/upcoming election is present
- results list driven by URL/query params so views are shareable
- loading, error, and empty states

### Race card component
Create a reusable MUI `Card` component for race summaries.

Each card should show:
- office title
- jurisdiction
- candidate names or measure summary
- mock tally visualization
- status chip
- source badge

Visualization guidance:
- use a compact MUI bar chart or custom progress bars for the mock tally preview
- keep the card readable even when there are many candidates; truncate and defer full detail to the detail page

### Race detail page
Create a detail page that expands the card into a full race view.

Include:
- election name/date
- office or measure title
- candidate list with party labels
- measure options where relevant
- source attribution
- mock tally section
- later hook point for the vote action and official-results comparison

### Empty state and local-race CTA
When no races are found for a location:
- show a clear empty state instead of a blank list
- explain that CivicMirror may not have imported that ballot yet
- provide an `Add a local race` call to action linked to the Phase 6 submission flow

### Public access expectations
- Browsing must stay fully available to unauthenticated users.
- Do not introduce a login wall for reading races, tallies, or race details.
- If the viewer is authenticated, the UI may show personalized hints, but public behavior must remain complete enough to browse without signing in.

## Deliverables Checklist
- [ ] Public `GET /api/races/` endpoint supports scope, state, ZIP, address, election, and certification filters
- [ ] Address and ZIP lookups resolve through on-demand Civic API calls with idempotent imports
- [ ] Redis caching added for `(address_normalized, election_id)`-style Civic lookups with a 1-hour TTL
- [ ] Race serializer returns election name, office title, jurisdiction, race type, candidates, mock vote count, certification status, and source badge data
- [ ] `GET /api/races/{id}/` provides full race detail and source attribution
- [ ] Public status display logic standardized to upcoming / results-pending / results-certified
- [ ] Querysets optimized with related-object loading and tally annotations
- [ ] Frontend home page default state shows national "What's Active Now" feed (no location required)
- [ ] IP geolocation auto-detects user's state on page load, shifts feed to statewide races, shows dismissible chip
- [ ] Filter bar implements National / State / ZIP / Address tabs with progressive location disclosure
- [ ] Location preference persisted in localStorage, restored on return visits
- [ ] Reusable MUI race card component implemented with tally preview, status chip, and source badge
- [ ] Race detail page created for full public browsing
- [ ] Empty state includes an `Add a local race` CTA leading into Phase 6
- [ ] Public browsing remains fully available without authentication
