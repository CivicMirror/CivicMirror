# Phase 8 Polish, Moderation, and Scale Readiness

## Goal
Harden CivicMirror for broader usage by improving moderation tooling, data export, accessibility, performance, and long-term platform features after the core browse-vote-compare loop is already working.

## Prerequisites
- Phases 1 through 7 complete

### Moderation tooling improvements
Build on the Phase 6 moderation queue with operator-focused tools:
- moderator dashboard summarizing pending submissions, rejected submissions, recent approvals, and abuse trends
- bulk approve/reject actions with audit logging
- spam detection flags for suspicious submissions
- abuse report endpoint so users can flag misleading or malicious community races

Recommended additions:
- moderator activity log
- duplicate-submission clusters
- simple heuristics for spam signals such as repeated URLs, repeated text blocks, or burst submissions from one account/IP

### Research data export
Create an admin-triggered export path for anonymized aggregate data.

Export requirements:
- CSV and JSON output formats
- mock vote tallies only, not individual vote records
- demographic breakdowns only at aggregate bucket level
- no usernames, account ids, raw addresses, or IP data in exports

Privacy guardrails:
- consider minimum-bucket thresholds so tiny demographic slices are suppressed
- log who generated each export and when
- document export retention and storage location

### Future auth roadmap: Google OAuth and Apple Sign-In
Plan a migration path from password-only accounts to social sign-in without breaking existing users.

Recommended direction:
- evaluate Django Allauth or social-auth integration
- keep `UserProfile` as the stable application identity layer
- support account linking so existing password users can attach a social provider later

### Email verification as a future enhancement
- treat email verification as optional for launch unless account recovery requires it sooner
- if added, use it for account recovery and security notifications, not as a proxy for real-world voter verification
- keep the terminology aligned: users are registered, not verified

### Embeddable race widgets
Add iframe-safe race widgets as a future-facing growth feature.

Requirements:
- dedicated minimal endpoint/page for embed rendering
- locked-down styling scope
- read-only race card with live tally summary
- no privileged auth flows inside the iframe
- CSP and frame-ancestor settings reviewed carefully

### Performance and scalability audit
After core functionality is stable, run a focused performance pass.

Areas to audit:
- ORM query plans with `select_related` / `prefetch_related`
- Redis cache hit rates and unnecessary misses
- Celery queue latency and task runtime hotspots
- heavy admin pages and report endpoints
- list/detail API response sizes

Expected outputs:
- prioritized query optimization backlog
- cache key review
- Celery profiling notes

### Accessibility
Perform a WCAG 2.1 AA audit across the React + MUI UI.

Required checks:
- keyboard navigation through filters, wizard steps, dialogs, and ballots
- screen-reader labels on form fields, chips, charts, and buttons
- visible focus states
- color contrast for party labels, status chips, and charts
- dialog and stepper semantics

Accessibility should be treated as a release blocker for core flows, not a later nice-to-have.

### Mobile future
Document the mobile roadmap rather than forcing it into launch scope.

Current direction:
- React Native app consuming the same DRF API
- keep auth/token, race list, race detail, vote, and profile endpoints mobile-safe
- migrate from DRF Token Auth to `djangorestframework-simplejwt` when the mobile client is built, as JWT better supports stateless multi-device auth

### Historical archive behavior
Past elections should remain part of the product experience.

Archive rules:
- keep past elections and races browsable after certification
- freeze historical comparison views after certification so later adapter changes do not rewrite displayed history without auditability
- clearly distinguish archived elections from currently active voting

### Observability for launch
For launch, observability is handled through server logs and a dedicated admin log viewer rather than third-party tools.

Launch posture:
- **Error tracking:** structured logs only. No Sentry or external error tracking at launch. The `ops` app admin panel includes a log viewer page surfacing sync failures, API errors, and moderation events.
- **Product analytics:** none at launch.
- **Uptime monitoring:** none at launch.
- **Admin alerts:** Civic sync failures and results-ingestion failures should surface in the admin `SyncLog` view and in server logs at a severity level that distinguishes them from routine info logs.

## Deliverables Checklist
- [ ] Moderator dashboard exists with pending queue visibility, bulk actions, and auditability
- [ ] Spam detection flags and abuse reporting flow added for community submissions
- [ ] Admin-triggered anonymized CSV/JSON research exports implemented without exposing individual user data
- [ ] Social-auth migration path documented for future Google OAuth / Apple Sign-In support
- [ ] Optional email verification plan defined for account recovery use cases
- [ ] Embeddable race widget design defined with iframe-safe constraints
- [ ] Performance audit completed for ORM usage, caching, and Celery workloads
- [ ] Accessibility audit performed against WCAG 2.1 AA for core flows
- [ ] Mobile roadmap documented around a future React Native client using the same DRF API
- [ ] Historical archive behavior defined so past elections remain browsable and comparison views stay stable
- [ ] Admin log viewer page implemented in the `ops` app for sync failures, API errors, and moderation events
