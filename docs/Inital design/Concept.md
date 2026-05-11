# CivicMirror — concept document

> **Informational and educational purposes only.** This platform is not affiliated with any government body, election authority, or official voting system. Mock votes cast here have no legal weight and do not represent or influence real election outcomes.

---

## MetaData

**Date:** 05/11/2026
**Concept by :** Walter LeFort
**Code by:** Claude AI and Copilot 


## Overview

CivicMirror is a web-based civic engagement platform that imports real election data and allows anyone — regardless of eligibility, location, or citizenship — to cast mock votes in real-world races. After official results are certified, the platform compares mock vote results against real outcomes, surfacing an unrestricted "internet public opinion" dataset alongside the official record.

The core research question: *when all eligibility restrictions are removed, how closely does open internet opinion reflect the choices of eligible voters?*

---

## Key concepts

### Elections vs races

These terms are distinct and map to separate data models.

An **election** is an administrative container — a scheduled date, a jurisdiction, and a label (e.g. "2026 Massachusetts General Election"). Users do not vote *in* an election; they vote in the individual races that belong to it.

A **race** (also called a contest) is the actual voteable unit — a specific office being decided, with its own candidates, jurisdiction, voting period, and results. A single election contains dozens to hundreds of races depending on the geographic area. Races come in two types:

- **Candidate race** — a set of named candidates competing for a single office (e.g. U.S. Senate — MA, 2026)
- **Ballot measure** — a yes/no question put to voters (e.g. Massachusetts Question 2)

All voting, result storage, and comparison logic operates at the race level. The election is used for grouping, browsing, and display only.

---

## User tiers

### Tier 1 — public (unauthenticated)

No account required. All of the following are available without logging in:

- Browse all current and upcoming races filtered by National, State, ZIP code, or address
- View live mock vote tallies for any race
- View certified official results once available, alongside the mock comparison
- Read candidate and race information sourced from the Google Civic API

Public users cannot cast mock votes.

### Tier 2 — verified (authenticated)

Users who complete a lightweight onboarding process gain voting access.

**Onboarding flow:**

1. Choose a username (user-defined or auto-generated) and password
2. Optionally provide basic demographic information (all fields nullable):
   - Age range
   - Country of residence
   - U.S. state of residence (if applicable)
   - Gender (optional)
3. Optional email for password recovery(warning about if not provided, password cannot be reset)
4. Accept terms of use (platform is for informational/educational purposes only)
5. Account is created — no email verification required at this time

**Username policy:** Users may choose their own username or accept a randomly generated one (e.g. `teal_osprey_4821`). Usernames are public-facing on nothing except their own profile page; no username is displayed alongside vote records.

**Password Policy**
- Minimal standards, no complex requirements needed at this time
- Ability to reset password if forgotten, and email is set
- Toggle View password on login page (open/close eye icon)

**Future authentication considerations:**
- Google OAuth login
- Apple Sign-In
- Email verification for account recovery
  

**What verified users can do:**
- Everything in Tier 1
- Cast one mock vote per race
- View their personal voting history
- Update demographic profile at any time
- Update password or Email 
- Include image or Avatar for profile.
  
---

## Ballot integrity

The platform uses a lightweight two-layer approach to limit stuffing without requiring email verification:

1. **One vote per account per race** — enforced at the database level. A user cannot change their vote once cast (mirrors real voting behavior).
2. **Rate limiting on account creation** — IP-based throttling on new account registrations to slow automated account farming.

Demographic self-report data (where provided) allows post-hoc filtering of results — e.g. "show results for U.S.-resident respondents only" or "18+ respondents only" — which significantly increases the research and comparison value of the dataset without requiring verified identity.

---

## Data sources

### Google Civic API

Primary source for election and race data. Used to populate:

- Active and upcoming elections
- Race/contest listings per jurisdiction
- Candidate names, parties, and office details
- Polling period dates

A scheduled sync job imports and refreshes this data on a regular interval.

### State-level official results

Where available, official certified results are ingested after election day using state-specific sources (APIs, open data portals, CSV/FTP feeds).

**Result certification notice:** Every race and election view displays a status indicator:

- `Results pending` — election has passed but official results have not yet been ingested
- `Results certified` — official results are available and the comparison view is active
- `Election upcoming` — voting period has not opened

### Local races — community contribution

Where no API or public data source covers a local race, verified users may submit a local race through a creation wizard. The submission process:

1. User initiates "Add a local race" from a location-filtered view
2. A modal wizard guides them through:
   - Race type (candidate or ballot measure)
   - Office title and jurisdiction (city/town, county, district)
   - Election date
   - Candidate names (for candidate races) or question text (for measures)
   - Source link (optional — e.g. local news article, municipal website)
3. The system checks for overlap against existing races with the same office, jurisdiction, and election date before accepting the submission
4. Submitted races are flagged as `community-contributed` in all views
5. Verified users may flag local elections to indicate errors in the data with a simple flag icon. A hoverover note on the flag to indicate it purpose.
6. Admin has the ability to adjust any communtiy race data if an error is detected or flagged

Community-contributed races do not have official results to compare against unless a verified user later submits a results source link for moderator review.

> The community race creation wizard is fully specified in a separate document: `local-race-wizard-spec.md`

---

## Application structure

### Views

**Home / race browser (public)**
- Filter bar: National / State / ZIP code / Address
- Race cards showing office, candidates, current mock tally, and status badge
- No authentication wall — full browsing is public


**Race detail page (public)**
- Full candidate list or ballot measure text
- Live mock vote chart
- Official result comparison (once certified)
- Status notice (pending / certified / upcoming)
- Source attribution (Civic API or community-contributed)

**Mock ballot / vote (verified users only)**
- Presented as a clean ballot card per race
- Single selection (candidate or yes/no)
- One-time submission — no edits after casting
- Confirmation screen after vote

**User profile (verified users only)**
- Username display
- Demographic info (editable)
- Personal vote history (list of races voted in, choices not publicly visible)

**Add local race wizard (verified users only)**
- Modal wizard — see `local-race-wizard-spec.md`

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Django (REST framework) |
| Task scheduling | Celery + Redis (election sync, result ingestion) |
| Database | PostgreSQL |
| Frontend | React + Vite + MUI v7 |
| State management | Zustand |
| Mobile (future) | React Native |

---

## Core data models (outline)

**Election**
- id, name, election_date, jurisdiction_level, state, source_id (Civic API), status

**Race**
- id, election (FK), race_type (`candidate` / `measure`), office_title, jurisdiction, geography_scope, voting_opens, voting_closes, certification_status, source (`civic_api` / `community`), submitted_by (FK, nullable)

**Candidate**
- id, race (FK), name, party, incumbent (bool)

**MeasureOption**
- id, race (FK), option_label (`Yes` / `No` / `Abstain`)

**MockVote**
- id, user (FK), race (FK), candidate or measure_option (FK), cast_at

**OfficialResult**
- id, race (FK), candidate or measure_option (FK), vote_count, vote_pct, certified_at, source_url

**UserProfile**
- id, user (FK), age_range, country, us_state, gender (all nullable), username, created_at

---

## Future considerations

- Google OAuth / Apple Sign-In
- Email verification for account recovery
- Moderator review queue for community-contributed races
- Research data export (anonymized CSV / JSON dataset)
- Embeddable race widgets for news sites and civic organizations
- Historical archive — past elections remain browsable and comparable indefinitely
- Mobile app (React Native)

---

## Framing and disclaimer

A persistent footer is displayed across all views and all authentication states:

> *CivicMirror is an informational and educational tool. Mock votes have no legal effect and do not influence real elections. This platform is not affiliated with any government agency, election authority, or political organization. Official election results displayed here are sourced from public records and are provided for reference only.*

---

*Document version: 0.1 — initial concept*
*Last updated: May 2026*