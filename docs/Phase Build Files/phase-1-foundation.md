# Phase 1 Foundation

## Goal
Establish the project skeleton, core schema, local infrastructure, and privacy/legal guardrails so every later phase can build on stable backend, frontend, and operations primitives instead of reworking fundamentals midstream.

## Prerequisites
- None beyond repository access and local development tooling
- Product agreement on the baseline CivicMirror concept: public browsing + registered mock voting

### Django project scaffold
- Create a Django project with a `config/` package and split settings into:
  - `config/settings/base.py`
  - `config/settings/dev.py`
  - `config/settings/prod.py`
- Use `django-environ` or `python-decouple` for environment-driven configuration. Recommended env vars:
  - `DJANGO_SECRET_KEY`
  - `DJANGO_DEBUG`
  - `DJANGO_ALLOWED_HOSTS`
  - `DATABASE_URL`
  - `REDIS_URL`
  - `CELERY_BROKER_URL`
  - `CELERY_RESULT_BACKEND`
  - `CORS_ALLOWED_ORIGINS`
  - `FRONTEND_BASE_URL`
- Create app boundaries early so responsibilities stay clear:
  - `accounts` for profile and auth-adjacent models
  - `elections` for Election, Race, Candidate, MeasureOption
  - `voting` for MockVote and vote APIs
  - `results` for OfficialResult and result ingestion
  - `integrations.civic` for Google Civic API client + sync tasks
  - `ops` for SyncLog, admin utilities, moderation helpers
  - `legal` for disclaimer/terms tracking
- Add `drf-spectacular` or equivalent OpenAPI generation from day one so frontend contracts are explicit.

### PostgreSQL setup and connection strategy
- Use PostgreSQL for all environments except tests where Django may use an isolated test database.
- In development, connect directly with `DATABASE_URL`.
- In production, assume connection pooling via PgBouncer in transaction mode.
- Django settings to establish immediately:
  - `CONN_MAX_AGE` enabled in prod behind PgBouncer
  - `ATOMIC_REQUESTS = False` globally; use targeted `transaction.atomic()` blocks around vote casting and imports
  - Statement timeout and idle-in-transaction timeout configured at the database layer
- Add indexes for expected hot paths:
  - `Election(source_id)`
  - `Race(election_id, race_status, certification_status)`
  - `Race(state, geography_scope)`
  - `MockVote(race_id)`
  - `OfficialResult(race_id)`
  - `UserProfile(username)` unique

### DRF baseline configuration
- Install and configure Django REST Framework with:
  - central router in `api/urls.py`
  - default pagination via `PageNumberPagination`
  - sane defaults such as `PAGE_SIZE = 25`
- Add global API defaults in `REST_FRAMEWORK`:
  - renderer/parser classes for JSON only at launch
  - authentication classes placeholder compatible with either TokenAuth or JWT
  - `DEFAULT_PERMISSION_CLASSES = [AllowAny]` with per-view overrides
  - throttling base config:
    - `anon`: conservative read limit
    - `user`: higher read limit
    - dedicated burst throttle buckets reserved for auth and vote endpoints later
- Normalize API error responses so frontend forms can reliably map field-level and non-field errors.

### Core data model schema
Create and migrate the baseline models in Phase 1 so later phases do not require destructive schema churn.

#### Election
- `id`
- `name`
- `election_date`
- `jurisdiction_level` (enum: `national`, `state`, `local`)
- `state` (nullable for national elections)
- `source_id` (Google Civic API election id)
- `status` (enum such as `upcoming`, `active`, `results_pending`, `results_certified`, `archived`)
- `last_synced_at` (nullable timestamp — set when Civic API last refreshed this election's races; used by the dynamic TTL cache check)

#### Race
- `id`
- `election` (FK → Election)
- `race_type` (enum: `candidate`, `measure`)
- `office_title`
- `jurisdiction`
- `geography_scope` (examples: `federal`, `statewide`, `county`, `city`, `district`)
- `voting_opens`
- `voting_closes`
- `certification_status` (enum: `upcoming`, `results_pending`, `results_certified`, `partial_results`)
- `source` (enum: `civic_api`, `community`)
- `submitted_by` (nullable FK for community submissions; may later be normalized to `UserProfile`)
- `race_status` (enum: `draft`, `pending_review`, `active`, `cancelled`, `archived`)
- `vote_method` (enum: `single_choice`, `multi_seat`, `ranked_choice`, `yes_no`)
- `max_selections` (default `1`; supports future multi-seat races)
- `last_synced_at` (nullable timestamp — set when Civic API last refreshed this race; drives the dynamic TTL staleness check in Phase 3)
- Recommended Phase 1 future-proofing fields:
  - `ocd_division_id`
  - `normalized_office_title`
  - `canonical_key` (unique, indexed)

#### Candidate
- `id`
- `race` (FK → Race)
- `name`
- `party`
- `incumbent` (bool)
- `candidate_status` (enum: `running`, `withdrawn`, `disqualified`, `write_in`)
- Optional nullable metadata fields worth adding now for community races:
  - `description`
  - `image_url`
  - `website_url`

#### MeasureOption
- `id`
- `race` (FK → Race)
- `option_label` (normally `Yes`, `No`, `Abstain`)

#### MockVote
- `id`
- `user` (FK → auth user)
- `race` (FK → Race)
- `candidate` (nullable FK → Candidate)
- `measure_option` (nullable FK → MeasureOption)
- `cast_at`
- Add a database check ensuring exactly one of `candidate` or `measure_option` is populated.

#### OfficialResult
- `id`
- `race` (FK → Race)
- `candidate` (nullable FK → Candidate)
- `measure_option` (nullable FK → MeasureOption)
- `vote_count`
- `vote_pct`
- `certified_at` (nullable)
- `source_url`
- Add nullable Phase 1 spike fields now to reduce later migration pain:
  - `result_type` (`official`, `unofficial`)
  - `is_winner`
  - `raw_payload` (JSON)
- The Phase 1 schema must explicitly support the later official-results spike by already carrying `vote_method`, `max_selections`, `candidate_status`, and `race_status` on related entities.

#### UserProfile
- `id`
- `user` (one-to-one FK → auth user)
- `age_range` (nullable)
- `country` (nullable)
- `us_state` (nullable)
- `gender` (nullable)
- `username` (unique public handle)
- `saved_zipcode` (nullable — registered users may optionally save their ZIP code for a default location view in the race browser; treated as PII, never displayed publicly, only used as a convenience preference)
- `created_at`

#### Legal/supporting models to add in Phase 1
- `TermsOfUseVersion`
  - `version`
  - `content_checksum`
  - `published_at`
  - `is_active`
- `TermsAcceptance`
  - `user`
  - `terms_version`
  - `accepted_at`
  - `ip_hash` (optional, hashed only if legal requires an audit trail)

### Canonical race dedup design
- Do not rely only on human-readable titles for deduplication.
- Build a canonical key from:
  - `source`
  - `Election.source_id`
  - normalized office title
  - `ocd_division_id`
  - `race_type`
  - `Election.election_date`
- Persist the canonical key on `Race` and enforce uniqueness where possible.
- This prevents duplicate imports when the same Civic contest is discovered from multiple representative addresses.

### Django admin from day one
Register all models in Django admin during Phase 1 so operations and moderation do not lag behind product features.

Recommended admin configuration:
- `ElectionAdmin`
  - `list_display`: name, election_date, jurisdiction_level, state, status, source_id
  - `search_fields`: name, source_id, state
  - `list_filter`: jurisdiction_level, status, state, election_date
- `RaceAdmin`
  - `list_display`: office_title, election, race_type, jurisdiction, state, source, race_status, certification_status
  - `search_fields`: office_title, jurisdiction, canonical_key, ocd_division_id
  - `list_filter`: race_type, source, race_status, certification_status, geography_scope
- `CandidateAdmin`
  - `list_display`: name, race, party, incumbent, candidate_status
  - `search_fields`: name, party, race__office_title
  - `list_filter`: incumbent, candidate_status, party
- `MeasureOptionAdmin`
  - `list_display`: option_label, race
  - `search_fields`: option_label, race__office_title
- `MockVoteAdmin`
  - `list_display`: user, race, cast_at
  - `search_fields`: user__username, race__office_title
  - `list_filter`: cast_at, race__race_type
- `OfficialResultAdmin`
  - `list_display`: race, candidate, measure_option, vote_count, vote_pct, certified_at
  - `search_fields`: race__office_title, candidate__name, source_url
  - `list_filter`: certified_at, race__certification_status
- `UserProfileAdmin`
  - `list_display`: username, user, country, us_state, created_at
  - `search_fields`: username, user__email, user__username
  - `list_filter`: country, us_state, created_at
- `TermsOfUseVersionAdmin` and `TermsAcceptanceAdmin` for legal auditability

### React + Vite + MUI v7 + Zustand scaffold
- Create a Vite React frontend with TypeScript.
- Install and wire:
  - `@mui/material` v7
  - `@mui/icons-material`
  - `@emotion/react` and `@emotion/styled`
  - `zustand`
  - `react-router-dom`
- Establish a shared theme file with typography, spacing, palette, and chip/status variants used across all phases.

### Frontend project structure
Use a simple, durable structure from the start:

```text
src/
  api/
    client.ts
    elections.ts
    auth.ts
    voting.ts
  components/
    layout/
    common/
    races/
  hooks/
    useAuth.ts
    useRaceFilters.ts
  pages/
    HomePage.tsx
    RaceDetailPage.tsx
    LoginPage.tsx
    RegisterPage.tsx
  store/
    authStore.ts
    raceFiltersStore.ts
  types/
  utils/
```

### API client wrapper
- Create a shared Axios instance or `fetch` wrapper with:
  - base URL from env (`VITE_API_BASE_URL`)
  - JSON defaults
  - auth header injection from the auth store
  - centralized 401 handling
  - request timeout
- Expose domain modules (`authApi`, `raceApi`, `voteApi`) instead of letting pages call raw HTTP directly.

### CI baseline
- Add GitHub Actions workflow(s) that run on pull requests and pushes:
  - backend: install dependencies, run `pytest`
  - frontend: install dependencies, run lint, run type check, optionally build
- Fail fast if migrations are missing by running `python manage.py makemigrations --check --dry-run`.
- Cache Python and Node dependencies to keep CI fast enough to be used continuously.

### Docker Compose local development
Create a compose stack for local onboarding with at least:
- `web` (Django API)
- `db` (PostgreSQL)
- `redis`
- `celery_worker`
- Optional but recommended immediately: `celery_beat`
- Mount code for live reload in development.
- Keep frontend either in its own service or run locally against the API; document the chosen path in the README.

### Production deployment target: GCP Cloud Run
The application deploys to Google Cloud Run with scale-to-zero.

Cloud Run deployment considerations:
- Django container must be stateless — no local filesystem writes, no sticky sessions.
- Static files served via GCS + Cloud CDN or a similar managed path rather than from the container.
- `CIVIC_API_KEY` and other secrets managed in GCP Secret Manager, mounted as environment variables to the Cloud Run service.
- Database: Cloud SQL (PostgreSQL) managed instance.
- Redis: GCP Cloud Memorystore (managed Redis).
- Celery workers run as a separate Cloud Run service or Cloud Run Job, sharing the same container image.

### Privacy, legal, and disclaimer architecture
Treat privacy/legal as foundational, not a polish task.

**Scope decisions for launch:**
- No formal privacy policy required before launch; the "no real effect" disclaimer is sufficient.
- GDPR/CCPA compliance is not in scope at launch (EU/CA user traffic not expected).

Required Phase 1 decisions and implementation hooks:
- Persistent disclaimer footer component on every frontend route:
  - clearly state votes are mock votes only
  - no legal or official effect
  - results are informational/community-generated unless marked certified
- Terms of use acceptance tracking is a first-class model, not a checkbox without storage.
- **Address handling:**
  - Raw address input from public users must never be persisted in PostgreSQL; use request-scope processing only.
  - Registered users may optionally save a ZIP code to `UserProfile.saved_zipcode` for a default location view; this is PII, never displayed publicly, and excluded from logs and analytics.
  - Only ZIP code and state are used for demographic metrics; raw street-level addresses are never stored.
  - Exclude any address data from logs, analytics payloads, and error traces.
- **Retention rules:**
  - Mock votes: retained indefinitely (no deletion policy at launch; revisit if storage costs increase).
  - Demographics: nullable and optional, used only in aggregate.
  - Account deletion workflow should anonymize personal profile fields while preserving aggregate vote counts.

### Development seed data
- Add a management command such as `seed_dev_data` that creates:
  - one upcoming election
  - a small set of candidate races and measure races
  - candidates and measure options
  - a few registered users and mock votes
- Seed data should be deterministic enough for screenshots, local QA, and frontend development.

## Deliverables Checklist
- [ ] Django project scaffold with split settings and environment-driven config
- [ ] Core Django apps created for accounts, elections, voting, results, integrations, ops, and legal concerns
- [ ] PostgreSQL configured with production-ready pooling assumptions and key indexes
- [ ] DRF installed with router, pagination defaults, and base throttling config
- [ ] Election, Race, Candidate, MeasureOption, MockVote, OfficialResult, and UserProfile models migrated
- [ ] Phase 1 schema includes future-proof fields for race status, vote method, max selections, and candidate status
- [ ] Django admin registered for all core and legal models with useful displays, search, and filters
- [ ] React + Vite frontend scaffolded with MUI v7 and Zustand
- [ ] Frontend folder structure established under `src/components`, `src/pages`, `src/store`, `src/api`, and `src/hooks`
- [ ] Shared API client wrapper created with base URL config and auth header injection hook
- [ ] GitHub Actions CI runs backend tests plus frontend lint/type-check
- [ ] Docker Compose local stack runs Django, PostgreSQL, Redis, and Celery services
- [ ] Privacy/legal foundations implemented: disclaimer footer, terms tracking, and non-persistent address handling
- [ ] Deterministic development seed script available for local setup
