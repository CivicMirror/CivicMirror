# Phase 5 Mock Voting

## Goal
Enable registered users to cast exactly one mock vote per race with strong backend validity guarantees, while keeping tallies public and laying the response shape needed for future demographic analysis.

## Prerequisites
- Phase 1 Foundation complete
- Phase 2 Authentication complete
- Phase 3 Google Civic API ingestion complete
- Phase 4 Public Race Browser complete

### Schema and database constraints
- Add a database-level unique constraint on `MockVote(user, race)`.
- Keep the check constraint from Phase 1 that enforces exactly one of `candidate` or `measure_option` is populated.
- Index `MockVote(race_id, cast_at)` to support tally queries.
- Do not expose update or delete behavior for mock votes.

### Vote casting endpoint
Create `POST /api/races/{id}/vote/` as the only write path for mock votes.

Request shape:

```json
{
  "candidate_id": 123
}
```

or

```json
{
  "measure_option_id": 456
}
```

Validation requirements:
- requester must be authenticated
- requester must be a registered user with a profile
- race must exist
- race must have `race_status = active`
- current time must satisfy `voting_opens <= now <= voting_closes`
- race must not be cancelled
- provided `candidate_id` or `measure_option_id` must belong to the target race
- user must not already have a vote in that race

### Transactional integrity
Perform vote creation inside a database transaction.

Recommended implementation details:
- wrap the endpoint in `transaction.atomic()`
- lock or re-read the target race in a consistent way before validating
- rely on the unique constraint to catch race-condition duplicates under concurrent requests
- convert `IntegrityError` into a stable API response such as `already_voted`

This endpoint is one of the most important integrity boundaries in the system; validation must live server-side even if the frontend disables invalid actions.

### Vote immutability
- Do not create update or delete endpoints for `MockVote`.
- Once cast, a mock vote is immutable.
- If policy ever changes later, treat vote changes as a new feature with explicit product/legal review; do not quietly add edit support.

### Public tally endpoint behavior
Tallies should be public and easy for the browser/detail pages to consume.

Options:
- include tally data directly in the race serializer for list/detail views
- or expose a dedicated `GET /api/races/{id}/tally/` endpoint and embed a summarized version in race detail

Minimum tally payload requirements:
- one row per candidate or measure option
- raw count
- percentage
- total mock votes

### Demographic-breakdown-ready response design
Even if the UI does not show filters yet, structure the tally response so future breakdowns do not require a breaking API redesign.

Recommended response shape:
- `totals`
- `options[]`
- `breakdowns` object with reserved keys such as:
  - `age_range`
  - `country`
  - `us_state`

For launch, these breakdown buckets may be empty or omitted unless specifically requested, but the serializer/service layer should anticipate the extension.

### Vote history endpoint
Create `GET /api/users/me/votes/` for the authenticated user.

Response should include:
- race id
- election name
- office title
- jurisdiction
- cast timestamp
- the user's own selected candidate/option
- current race status

Privacy rule:
- a user's choice is visible only to that user in this endpoint
- no public endpoint should reveal who voted for whom

### Race serializer integration
For authenticated viewers, the race detail response can optionally include:
- `viewer_has_voted`
- `viewer_choice`

Do this only on detail views or cheap query paths to avoid heavy list-query fanout.

### Frontend ballot UX
Build a focused ballot experience for race detail pages.

**Voting method for launch: single choice (first past the post).** Ranked-choice voting is a future enhancement and not in scope for launch.

Candidate display rules:
- Display a maximum of 10 candidates per race, including any write-in candidates.
- Highlight the top 2 candidates by current mock vote count with a visual distinction (bold label or accent chip).
- If a race has more than 10 candidates, show a note explaining the display cap.
- Write-in candidates are stored as `Candidate` rows with `candidate_status = write_in` and count against the 10-candidate cap. The ballot includes a write-in option below the named candidates. If the race is already at 10 candidates, a note is shown instead of the write-in input.

Required pieces:
- ballot card component
- clean single-selection UI using MUI `RadioGroup`
- write-in text field rendered as the last option below named candidates
- submit button with disabled/loading states
- confirmation dialog before final submission
- success state after vote cast

### Already-voted state
When the authenticated user already voted:
- replace the ballot form with an `already voted` panel
- show the user's recorded choice
- keep public tally visualization visible
- make it clear the vote cannot be changed

### Tally visualization
Use a simple, readable visualization on the frontend:
- grouped bars, horizontal bars, or percentage pills
- show counts and percentages together when possible
- support both candidate races and yes/no measure races without separate page architectures

### Error handling expectations
Return explicit, stable backend error codes for common invalid vote attempts:
- `not_authenticated`
- `race_inactive`
- `voting_closed`
- `invalid_option`
- `already_voted`

The frontend should translate these into user-friendly messages, but the API contract should stay machine-readable.

## Deliverables Checklist
- [ ] `MockVote(user, race)` unique constraint enforced at the database level
- [ ] Vote-casting endpoint `POST /api/races/{id}/vote/` implemented for registered users
- [ ] Vote validation checks race activity, voting window, race status, option ownership, and prior votes
- [ ] Vote creation runs inside a DB transaction and handles duplicate submissions safely
- [ ] No update/delete endpoints exist for mock votes, preserving immutability
- [ ] Public tally data is exposed per candidate/measure option with counts and percentages
- [ ] Tally response shape leaves room for future demographic breakdowns
- [ ] `GET /api/users/me/votes/` returns the authenticated user's vote history only
- [ ] Frontend ballot card built with single-selection MUI controls and confirmation dialog
- [ ] Already-voted UI state shows the user's choice and blocks changes
- [ ] Tally visualization added to race detail and/or list views
- [ ] API error responses for invalid vote attempts are explicit and stable
