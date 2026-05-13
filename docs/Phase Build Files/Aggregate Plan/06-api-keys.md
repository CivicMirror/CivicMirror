# API Keys — Status and Acquisition Guide

> **Status: ✅ ALL KEYS ACTIVE** — Google Civic, OpenFEC, Open States, and GitHub Token all configured. Added to `backend/.env.example` for developer onboarding.

## Overview

This document tracks the API key status for each data source and provides instructions for obtaining keys where they are still needed.

> **Security note:** Never commit API keys to the repository. Keys are stored locally in `docs/Secrets/API-Keys.md` (git-ignored) and injected as environment variables in production via Cloud Run secrets or Secret Manager.

---

## Key Status by Source

| Source | Key Required? | Status | Env Var Name |
|---|---|---|---|
| Google Civic Information API | Yes | ✅ Active | `CIVIC_API_KEY` |
| OpenFEC API | Yes | ✅ Active | `FEC_API_KEY` |
| Open States API | Yes | ✅ Active | `OPENSTATES_API_KEY` |
| congress-legislators (GitHub raw) | No | ✅ No key needed | — |
| U.S. Census Geocoder | No | ✅ No key needed | — |
| Open Civic Data division IDs | No | ✅ No key needed | — |
| OpenElections (GitHub) | No (optional) | ✅ Active (optional boost) | `GITHUB_TOKEN` (optional) |
| MEDSL / Harvard Dataverse | No | ✅ No key needed | — |

**All required keys are already in the project, including a GitHub token for OpenElections ingestion.** No new paid accounts or applications are needed for the Tier 1 or Tier 2 integration plan.

---

## Source Details

### Google Civic Information API
- **Registration:** Google Cloud Console → Enable `Civic Information API` on the project
- **Key location:** Already configured in production as `CIVIC_API_KEY`
- **Free quota:** 25,000 requests/day
- **No action needed**

### OpenFEC API
- **Registration:** `https://api.data.gov/signup/`
  - Click "Get an API key"
  - Registration is instant and free
  - The key grants access to all `api.data.gov` services including OpenFEC
- **Key location:** Already obtained; stored in `docs/Secrets/API-Keys.md`
- **Free quota:** 1,000 requests/hour, 10,000 requests/day
- **Env var to add to production:** `FEC_API_KEY`
- **No new registration needed**

### Open States API
- **Registration:** `https://openstates.org/accounts/profile/` after creating a free account
- **Key location:** Already obtained; stored in `docs/Secrets/API-Keys.md`
- **Free quota:** 500 requests/day
- **Env var to add to production:** `OPENSTATES_API_KEY`
- **No new registration needed**

### OpenElections GitHub (GITHUB_TOKEN)
- The `openelections` organization repos are fully public
- Unauthenticated GitHub API access: 60 requests/hour
- **A GitHub personal access token has been created and added to `docs/Secrets/API-Keys.md`**
  - Scope: `public_repo` (read-only, public repos)
  - Raises rate limit to 5,000 requests/hour
- **Status: ✅ Ready to use**

---

## Environment Variable Checklist

When implementing, ensure the following env vars are added to all environments (local `.env`, Cloud Run secrets, CI/CD secrets):

```bash
# Already configured
CIVIC_API_KEY=<existing key>

# Add for new integrations
FEC_API_KEY=<from docs/Secrets/API-Keys.md>
OPENSTATES_API_KEY=<from docs/Secrets/API-Keys.md>
GITHUB_TOKEN=<from docs/Secrets/API-Keys.md>  # ✅ created and stored
```

Add these to `backend/.env.example` (without values) so all developers know to configure them.

---

## Sources That Do NOT Need Keys

The following sources work without any authentication:

| Source | Access Method |
|---|---|
| congress-legislators | Direct HTTPS download from `theunitedstates.io` GitHub raw |
| U.S. Census Geocoder | REST API, no key required |
| OCD division IDs | GitHub raw CSV download |
| MEDSL / Harvard Dataverse | Dataverse public API / direct CSV download |
| OpenElections CSV files | GitHub raw content download |

---

## No New Paid Accounts Required

All sources in the Tier 1 and Tier 2 implementation plan are free or already paid for. The only potential cost increase:
- **Open States:** If sync needs exceed 500 requests/day, the paid tier starts at $10/month for 5,000 requests/day. Given the nightly-per-state strategy (estimated 150–250 requests/day), this is unlikely to be needed.
- **FEC API:** Free with no usage-based cost beyond the 1,000 req/hour rate limit. No upgrade needed.

---

## Adding Keys to Production (Cloud Run)

When implementing, the new keys must be added to Google Cloud Secret Manager and mapped as environment variables in the Cloud Run service:

```bash
# Create secrets (one-time)
echo -n "$FEC_API_KEY" | gcloud secrets create fec-api-key --data-file=-
echo -n "$OPENSTATES_API_KEY" | gcloud secrets create openstates-api-key --data-file=-
echo -n "$GITHUB_TOKEN" | gcloud secrets create github-token --data-file=-

# Grant access to Cloud Run service account
gcloud secrets add-iam-policy-binding fec-api-key \
  --member="serviceAccount:<run-sa>@<project>.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Map into Cloud Run service (update deploy command or Terraform)
# --set-secrets FEC_API_KEY=fec-api-key:latest
# --set-secrets OPENSTATES_API_KEY=openstates-api-key:latest
# --set-secrets GITHUB_TOKEN=github-token:latest
```

See existing Terraform config in `terraform/` for how `CIVIC_API_KEY` is currently managed — follow the same pattern.

---

## Back to Index

[README.md](README.md) — Plan index and summary.
