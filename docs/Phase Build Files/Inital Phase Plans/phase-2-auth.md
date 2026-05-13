# Phase 2 Authentication and Registered User Flows

## Goal
Add account creation, login, token/session management, and user profile editing so CivicMirror can distinguish public browsing from registered-user actions such as mock voting and local race submission.

## Prerequisites
- Phase 1 Foundation complete
- Core models, admin, CI, and frontend scaffolding working end to end

### Identity model and profile ownership
- Keep Django's built-in `User` model for authentication credentials unless a strong reason emerges to swap before launch.
- Extend user-facing identity through `UserProfile` as a one-to-one model.
- Create profiles at registration time inside the same transaction as user creation; avoid relying only on signals for critical data integrity.
- Public-facing identity comes from `UserProfile.username`, not the Django username field unless the team intentionally aligns them.

### Registration endpoint contract
Create `POST /api/auth/register/` with payload and validation shaped for launch needs:

```json
{
  "username": "optional_custom_name",
  "password": "user_password",
  "age_range": "optional",
  "country": "optional",
  "us_state": "optional",
  "gender": "optional",
  "terms_version": "2025-01",
  "terms_accepted": true
}
```

Registration rules:
- `password` is required and validated with Django password validators.
- `terms_accepted` must be true.
- `terms_version` must point to the active terms record.
- Demographic fields are optional and nullable.
- `username` may be user-supplied or auto-generated.
- If the user does not provide a username, generate one automatically.
- If a provided username is taken or blocked, return a field error.
- Return the created profile plus auth credentials/token payload needed by the frontend.

### Username generation utility
Implement a dedicated username generator, not inline serializer logic.

Recommended format:
- `adjective_noun_4821`
- Example: `teal_osprey_4821`

Generator requirements:
- Source from curated adjective and noun lists committed to the repo
- Remove profanity, slurs, political figures, and brand-sensitive terms from the wordlist
- Normalize to lowercase snake_case
- Append a random 4-digit suffix
- Retry on uniqueness collision
- Keep the utility reusable from registration and admin tooling

### Registration abuse prevention
- Apply IP-based rate limiting to registration using `django-ratelimit`, DRF throttling, or both.
- Recommended launch posture:
  - burst limit for repeated registration attempts from one IP
  - daily cap for account creation from one IP
- Log throttled attempts in a structured way without storing raw passwords or other sensitive payloads.
- Consider adding a soft blocklist mechanism for obviously abusive usernames.

### Login, logout, and token management

**Decision: DRF Token Auth for launch.** JWT is the preferred upgrade path when a mobile app is built (Phase 8), but DRF's built-in token model is simpler to operate at launch scale.

DRF Token Auth implementation:
- `POST /api/auth/login/` creates or returns the user's token alongside basic user/profile data.
- `POST /api/auth/logout/` deletes the token server-side.
- Token expiry: **30 days.** Implement using `django-rest-knox` (supports per-token expiry and multi-device revocation) or a custom middleware that checks `created` on the token row. Delete expired tokens on login or via a scheduled cleanup task.
- The frontend auth store holds the token in memory and persists it in `localStorage`; `Authorization: Token <value>` is injected on every authenticated request.

Mobile upgrade path (Phase 8):
- When a React Native client is built, migrate from DRF Token Auth to `djangorestframework-simplejwt`.
- Keep `UserProfile` as the stable identity layer so the token strategy can swap without disrupting vote history or profile data.

### Permissions and auth guards
- Use DRF `IsAuthenticated` for any endpoint that creates votes, edits a profile, or submits local races.
- Add a lightweight custom permission such as `IsRegisteredUser` only if there is logic beyond basic authentication.
- Keep public race browsing explicitly open to unauthenticated users.
- Ensure backend permissions mirror frontend route guards; never rely on the UI alone.

### Terms acceptance tracking
- Store acceptance in `TermsAcceptance` with:
  - `user`
  - `terms_version`
  - `accepted_at`
- Registration must fail if there is no active terms version to accept.
- Future terms changes should not silently overwrite history; store one row per accepted version.

### UserProfile CRUD endpoint
Expose `GET/PATCH /api/users/me/profile/` for the authenticated user.

Allowed updates:
- `age_range`
- `country`
- `us_state`
- `gender`

Not editable after initial set without a special admin flow:
- `username`

Recommended API behavior:
- return the full current profile on GET
- PATCH only editable fields
- reject username mutation with a clear validation error

### Frontend auth architecture
Build auth as shared infrastructure, not page-local state.

Recommended frontend pieces:
- `authStore` in Zustand containing:
  - auth status
  - current user/profile
  - auth token
- `AuthProvider` or bootstrap hook that restores auth on app load from `localStorage`
- `login`, `register`, and `logout` actions centralized in the store/API layer
- `ProtectedRoute` wrapper for registered-only pages such as vote history and local race submission

### Login and registration forms
- Use `react-hook-form` + `zod` for both login and registration.
- Registration form fields:
  - username (optional)
  - password
  - optional demographics
  - required terms checkbox
- Keep demographic fields clearly optional and explain why they are collected.
- Surface backend field errors directly under form controls.

### API and UX details to lock down early
- Decide whether login accepts username only or username/email later.
- Return enough user metadata on login for the frontend to render the signed-in state immediately.
- On auth expiration, clear local auth state and route back to login only for protected actions; public browsing should continue uninterrupted.
- Keep the naming consistent everywhere: use `registered` instead of `verified` because no identity verification occurs.

## Deliverables Checklist
- [ ] Registration endpoint created with required terms acceptance and optional demographics
- [ ] Username generation utility implemented with filtered adjective/noun wordlists and collision handling
- [ ] IP-based rate limiting applied to registration and auth abuse paths
- [ ] Login/logout endpoints implemented with a documented token strategy
- [ ] Token Auth implemented with DRF's built-in token model; expiry policy documented and applied
- [ ] `TermsAcceptance` records store accepted version and timestamp for every registered account
- [ ] `GET/PATCH /api/users/me/profile/` supports demographic edits while keeping username immutable
- [ ] DRF permissions protect registered-only actions without affecting public browsing
- [ ] Frontend auth store built with Zustand and app bootstrap logic
- [ ] Login/register forms implemented with react-hook-form + zod
- [ ] Protected route handling added for registered-only pages
- [ ] Terminology aligned on `registered user` across backend, frontend, and documentation
