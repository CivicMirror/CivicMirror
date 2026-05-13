# Phase 6 Local Race Submission Wizard

## Goal
Let registered users submit missing local races through a structured wizard, while ensuring every community-submitted race enters a moderation queue before it can appear in the public browser.

## Prerequisites
- Phase 1 Foundation complete
- Phase 2 Authentication complete
- Phase 3 Google Civic API ingestion complete
- Phase 4 Public Race Browser complete
- Phase 5 Mock Voting complete

### Moderation-first community race model
Community submissions must not go public immediately.

Required rule:
- all community-submitted races start with `community_status = pending_review`
- they are not visible in the public race browser until a moderator promotes them to `community_status = active`

Add or normalize the following model fields for community races:
- `community_status` (`pending_review`, `active`, `rejected`)
- `submitter` (FK to `UserProfile`; if `submitted_by` already exists from Phase 1, migrate or alias it to the profile-centric model)
- `submitted_at`
- `source_links` (JSON array of URLs)
- `location_name` (for example `Town Hall`)
- `moderator_notes`

Recommended supporting fields:
- `reviewed_at`
- `reviewed_by`
- `rejection_reason` or a structured moderator decision code

### Additional schema for wizard data
The wizard captures richer community-specific content than Civic imports.

Plan for storage of:
- candidate-level nullable metadata:
  - `description`
  - `image_url`
  - `website_url`
- measure-level explanatory content:
  - yes-vote details
  - no-vote details
  - supporting links

Implementation options:
- extend `Candidate` with nullable metadata fields
- add a JSON field on `Race` for community-only measure details
- keep public serializers strict so only approved content is displayed

### Public visibility rules
Public browser queries must filter community races with:
- `source = community`
- `community_status = active`
- `race_status = active`

Pending or rejected submissions must never appear in public lists or search results.

### Overlap detection and conflict warning
Before accepting a submission, query for likely duplicates using:
- normalized `office_title`
- `jurisdiction`
- `election_date`

Recommended behavior:
- if an overlap is found, return a conflict warning payload to the user
- allow the UI to show the existing race and ask the user to confirm they still want to submit
- still route the submission to moderation if duplicates are plausible rather than silently discarding it

Expand overlap checks where possible with:
- `location_name`
- source links
- existing community pending-review races

### Submission API contract
Create a single server-validated endpoint:
- `POST /api/races/local/`

Use one final payload rather than partial per-step persistence at launch.

Server-side responsibilities:
- validate the full payload
- ensure the requester is authenticated
- attach the submitter profile
- force `source = community`
- force `community_status = pending_review`
- set `race_status = pending_review` until moderation promotes it
- create candidate or measure records transactionally

### Wizard flow: Step 1
#### Race type selection
- Toggle between:
  - `Candidate Race`
  - `Ballot Measure`
- This step determines later fields and validation branches.

### Wizard flow: Step 2 for candidate races
Collect:
- office title
- jurisdiction (`city`, `town`, `county`, `district`)
- election date
- location name

Validation:
- required fields present
- election date must be in the future
- title and jurisdiction trimmed and normalized

### Wizard flow: Step 2 for ballot measures
Collect:
- ballot type (`Citizen-Initiated`, `Town-Initiated`)
- question title
- voting date
- location

Validation:
- voting date in the future
- question title long enough to distinguish measures clearly

### Wizard flow: Step 3 for candidate races
Allow multiple candidates with fields:
- name
- party
- brief description
- image URL (URL input only — no file uploads)
- website URL
- candidate type toggle (`running` or `write_in`)

Validation:
- at least one candidate required
- candidate count capped at 10 total (including write-ins); the "Add candidate" button is disabled and a note is shown when the limit is reached
- candidate names unique within the submission
- URLs must be valid and normalized

### Wizard flow: Step 3 for ballot measures
Collect:
- yes vote details
- no vote details
- additional info links (multiple allowed)

Validation:
- yes/no detail blocks cannot both be blank
- links must be valid URLs

### Wizard flow: Step 4 review and submit
- show a read-only summary of every prior step
- surface duplicate warnings from the API if present
- require a final acknowledgment that the submission may be rejected or edited by moderators before publication

### Frontend validation with react-hook-form + zod
- Use a Zod schema per step.
- Add cross-field validation such as:
  - election date must be in the future
  - candidate race must include candidates
  - ballot measure must include yes/no explanatory content
  - source links must be valid URLs
- Keep step-level schemas composable into the final full-payload schema.

### Wizard UI implementation
Build the wizard with MUI `Stepper` and explicit progress affordances.

Required UX elements:
- progress indicator
- back/forward navigation
- field-level error messaging
- save only in client state until final submit
- disable final submit while invalid or submitting

### Submission success behavior
After a successful submit:
- show a clear confirmation message: `Your race is under review`
- do not show the race in the public browser yet
- optionally link the user to a `My submissions` page later, but this is not required for launch

### Community badge rules
Use explicit public badges:
- `community-contributed • pending review` for private submitter/admin views only
- `community-contributed` once the race is approved and active

Do not leak rejected or pending moderation state into public discovery pages.

### Django admin moderation workflow
Add admin support for community moderation from this phase, not later.

**Moderators are admin users only for launch.** A tiered moderator role can be added later if system demand warrants it.

Required admin features:
- dedicated race management page listing all community submissions, defaulting to **oldest submitted first** (`submitted_at ASC`) so backlogged reviews are surfaced at the top
- list filter for `community_status = pending_review`
- bulk approve action
- bulk reject action with required `rejection_reason` field
- display submitter, submitted_at, and overlap warnings where available
- editable moderator notes

Approval behavior:
- set `community_status = active`
- set `race_status = active`
- optionally stamp reviewer metadata

Rejection behavior:
- set `community_status = rejected`
- keep the content hidden from public views
- a rejection notice appears in the submitter's profile using the `rejection_reason` value: "Sorry, your race was rejected for: [reason]." Visible only to the submitting user.

### Race auto-close and admin override
Community races automatically close 2 weeks after the official election date.

Auto-close behavior:
- a scheduled task sets `race_status = archived` for any community race that is still `active` and whose `election.election_date + 14 days` has passed
- voting closes on archived races; past mock votes and tallies remain viewable
- admin retains the ability to manually reopen a race and update or add official results from the race admin detail page

## Deliverables Checklist
- [ ] Community-submitted races default to `community_status = pending_review` and stay hidden from public browsing
- [ ] Community race schema includes submitter, submitted timestamp, source links, location name, and moderator notes
- [ ] Candidate/measure metadata needed by the wizard has a concrete storage design
- [ ] Public race queries exclude pending-review and rejected community submissions
- [ ] Overlap detection warns on likely duplicate races before submission is finalized
- [ ] Single endpoint `POST /api/races/local/` validates and creates community submissions server-side
- [ ] Multi-step frontend wizard implemented with react-hook-form, zod, and MUI Stepper
- [ ] Step validation includes future-date and cross-field rules
- [ ] Submission success flow clearly tells the user the race is under review
- [ ] Community badges differentiate active community content from pending-review content in appropriate contexts
- [ ] Django admin exposes a moderation queue with approve/reject bulk actions
- [ ] Moderation approval moves races from pending review to active visibility
