# Developer Questions

Decisions resolved here are reflected in the corresponding phase files. Remaining open questions are noted below each section.

## Authentication

- **Token auth vs JWT — RESOLVED:** DRF Token Auth for launch. JWT is the preferred upgrade path when a mobile client is built (Phase 8). See phase-2-auth.md.
- **Session duration / token expiry policy — RESOLVED:** 30-day token expiry.

## Civic API Coverage

- **Seeding strategy — RESOLVED:** The Google Civic API's `/elections` endpoint lists elections but returns no race data. Races only come from `voterInfoQuery`, which requires an address + electionId. Chosen approach: seed with all 50 state capitals + DC at sync time for statewide/federal coverage; expand on-demand when users query by ZIP or address. New races are persisted to DB and served from cache on subsequent hits. See phase-3-civic-api.md.
- **Default home view UX — RESOLVED:** National "What's Active Now" feed on page load. IP geolocation silently auto-detects state and shifts to statewide races. ZIP/address unlocks full local coverage. See phase-4-race-browser.md.
- **Fallback when Civic API returns no contests — RESOLVED:** Show seeded statewide races for that state + local race wizard CTA ("Don't see your race? Add it.").
- **Election/race lifecycle after voting closes — RESOLVED:** Races are archived after official results are processed. Results remain viewable but voting is closed. Admin can reopen a race and add official results manually. See phase-7-official-results.md.
- **Address storage — RESOLVED:** Public queries never persist raw addresses (request-scope only). Registered users may optionally save a ZIP code to their profile for a default location view; treated as PII, never shown publicly. Only ZIP/state used for demographic metrics. See phase-1-foundation.md and phase-2-auth.md.

## Data Model

- **Ranked-choice voting — RESOLVED:** Single choice (first past the post) for launch. Ranked choice is a future enhancement.
- **Maximum candidates per race — RESOLVED:** Capped at 10 for display. Top 2 by mock vote count are highlighted. A note is shown if the race has more than 10 candidates.
- **Write-in candidates — RESOLVED:** Supported in mock voting. Counts against the 10-candidate display cap. A note is shown if adding a write-in would exceed the limit.

## Moderation

- **Moderator role — RESOLVED:** Admin-only for launch. A separate moderator tier can be introduced if system demand warrants it.
- **Race review turnaround — RESOLVED:** Community races auto-archive 2 weeks after the official election date. Admin can reopen and add official results. Admin race list defaults to oldest-open-first. See phase-6-local-race-wizard.md.
- **Rejected submission notification — RESOLVED:** A rejection note appears in the submitter's profile using the admin-supplied `rejection_reason`: "Sorry, your race was rejected for: [reason]." No email required.

## Infrastructure

- **Deployment target — RESOLVED:** GCP Cloud Run with scale-to-zero.
- **`CIVIC_API_KEY` management — RESOLVED:** GCP Secret Manager, mounted as an environment variable to the Cloud Run service.
- **Redis instance — RESOLVED:** GCP Cloud Memorystore (managed Redis).
- **Target initial scale — RESOLVED:** Unknown at launch; monitor via GCP metrics and scale accordingly.

## Media & Storage

- **Candidate images — RESOLVED:** URL input only. No file upload or cloud storage at launch.

## Legal & Privacy

- **Formal privacy policy — RESOLVED:** Not required before launch. Disclaimer footer + terms acceptance is sufficient.
- **Data retention — RESOLVED:** Mock votes retained indefinitely. Revisit if storage costs become an issue.
- **"No real effect" disclaimer — RESOLVED:** Sufficient. No legal review required at launch.
- **GDPR/CCPA — RESOLVED:** EU/CA users not expected at launch. Consent and deletion workflows not in scope.

## Analytics & Observability

- **Error tracking — RESOLVED:** Structured logs only. Admin panel includes a log viewer page (`ops` app) for sync failures, API errors, and moderation events. No Sentry at launch.
- **Product analytics — RESOLVED:** None at launch.
- **Uptime monitoring — RESOLVED:** None at launch.

## Testing

- **Test coverage target — RESOLVED:** No minimum coverage percentage enforced.
- **E2E testing — RESOLVED:** Not in scope for launch.
- **Staging environment — RESOLVED:** No dedicated staging environment at launch.
