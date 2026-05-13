# Orchestration Layer — Matcher and Enrichment Services

> **Status: ✅ IMPLEMENTED** — `RaceMatcher`, `CandidateMatcher`, `EnrichmentMerger`, `SourceRecordStore` all built and tested. Post-review fixes: At-Large House district matching and FEC first-request throttle delay corrected.

The orchestration layer sits between the source adapters and the core Django models. It handles:
- Cross-source race and candidate identity matching
- Safe enrichment (field-level priority rules)
- Conflict detection and flagging
- Unified write path

---

## Module Location

```
backend/integrations/orchestrator/
  __init__.py
  race_matcher.py      ← canonical race identity resolution
  candidate_matcher.py ← cross-source candidate identity resolution
  enrichment.py        ← field-level merge rules per source priority
  source_store.py      ← SourceRecord upsert and checksum logic
  exceptions.py        ← MatchConflict, AmbiguousMatchError, etc.
```

---

## 1. `RaceMatcher`

Resolves whether an incoming raw race record matches an existing `Race`, and if so, which one.

### Match Tiers (in order)

1. **Exact canonical_key match** — if the incoming record is from the same source that created the canonical key, use exact match
2. **OCD division ID + office type + election date match** — primary cross-source dedup
3. **State + normalized office title + district number + election date** — fallback if OCD ID is unavailable
4. **Low-confidence: normalized title + state + approximate date** — flagged as `match_confidence='low'`
5. **No match** — create new Race with confidence label appropriate to source

### Confidence Assignment

| Match tier | `match_confidence` |
|---|---|
| Source-own canonical_key | `verified` |
| OCD ID + office type + date | `high` |
| State + title + district + date | `medium` |
| Title + state only | `low` |
| No match, new primary source | `verified` (new authoritative record) |
| No match, enrichment source | `flagged` (needs admin review) |

### Interface

```python
class RaceMatcher:
    def find_or_create(
        self,
        source: str,
        external_id: str,
        normalized_payload: dict,
        district_records: list[DistrictRecord],
    ) -> tuple[Race, bool]:
        """
        Returns (race, created).
        Sets match_confidence on the race.
        If match_confidence is 'low' or 'flagged', sets race_status to 'pending_review'.
        """
```

---

## 2. `CandidateMatcher`

Resolves whether an incoming candidate record from an enrichment source matches an existing `Candidate`.

### Match Tiers (in order)

1. **External ID match** — `fec_candidate_id`, `bioguide_id`, or `openstates_person_id` already set
2. **Cross-reference IDs** — e.g., congress-legislators provides FEC IDs; if FEC ID matches a `Candidate.fec_candidate_id`, it's the same person
3. **Normalized name + race match** — normalized candidate name within the same `Race`
4. **Normalized name + office + state** — for enrichment sources that don't know the specific Race

### Field-Level Priority Rules

When a match is found, enrichment fields follow source priority. The rule is: **do not overwrite fields already set by a higher-priority source unless the value is demonstrably stale or empty.**

| Field | Priority |
|---|---|
| `name` | Civic (ballot name) — do not overwrite |
| `party` | Civic → FEC → Open States → congress |
| `incumbent` | Civic → congress-legislators → Open States |
| `image_url` | Civic → Open States (only if Civic is blank) |
| `website_url` | Civic → congress → Open States |
| `description` | Civic → congress (bio field) |
| `contact_phone` | congress-legislators → Open States |
| `contact_office` | congress-legislators → Open States |
| `fec_candidate_id` | FEC (set once; do not overwrite) |
| `bioguide_id` | congress-legislators (set once) |
| `openstates_person_id` | Open States (set once) |

### Interface

```python
class CandidateMatcher:
    def enrich(
        self,
        race: Race,
        source: str,
        external_id: str,
        enrichment_payload: dict,
    ) -> tuple[Candidate | None, str]:
        """
        Returns (candidate, action) where action is one of:
          'enriched'       — match found, fields updated
          'no_match'       — no candidate found for this race (skip)
          'ambiguous'      — multiple candidates could match (flagged)
          'skipped'        — no enrichable fields changed
        """
```

---

## 3. `EnrichmentMerger`

Applies field-level merge rules when updating an existing record. Enforces source priority; never blindly overwrites.

### Merge Logic

```python
def merge_candidate_fields(candidate: Candidate, source: str, payload: dict) -> dict:
    """
    Returns a dict of fields safe to update for this source.
    Respects field-level priority: skips fields already set by a higher-priority source.
    """
```

**Priority order:** `civic_api` > `fec` > `congress` > `openstates`

### Source Metadata Merge

`source_metadata` is always merged by source key, never replaced:
```python
candidate.source_metadata = {
    **candidate.source_metadata,
    source: enrichment_payload['metadata'],
}
```

---

## 4. `SourceRecordStore`

Manages `SourceRecord` creation and checksum-based change detection.

### Interface

```python
class SourceRecordStore:
    def upsert(
        self,
        source: str,
        external_id: str,
        raw_payload: dict,
    ) -> tuple[SourceRecord, bool]:
        """
        Returns (record, changed).
        'changed' is True if the payload differs from the stored checksum.
        Use 'changed' to decide whether to re-run enrichment.
        """
```

### Checksum Logic

```python
import hashlib, json

def _checksum(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()
```

Incremental sync: if `changed=False`, the adapter skips the record without writing to models. The `SyncLog.records_skipped` counter is incremented instead.

---

## 5. Typical Orchestration Flow: FEC Candidate Enrichment

```
sync_fec_candidates(cycle_year=2024)
  for each state in US_STATES:
    raw_candidates = fec_client.list_candidates(office='H', state=state, cycle=2024)
    for raw in raw_candidates:
      # 1. Check SourceRecord; skip if unchanged
      record, changed = source_store.upsert('fec', raw['candidate_id'], raw)
      if not changed:
          sync_log.records_skipped += 1
          continue

      # 2. Map raw to normalized enrichment dict
      payload = fec_mapper.map_candidate(raw)

      # 3. Resolve district via Census
      district = census_resolver.resolve_ocd_id(
          state=payload['state'],
          office_type='H',
          district=payload['district'],
      )

      # 4. Find matching Race
      race, created = race_matcher.find_or_create(
          source='fec',
          external_id=payload['fec_election_id'],
          normalized_payload=payload,
          district_records=[district],
      )

      # 5. Enrich Candidate
      candidate, action = candidate_matcher.enrich(
          race=race,
          source='fec',
          external_id=payload['candidate_id'],
          enrichment_payload=payload,
      )

      # 6. Log outcome
      if action in ('enriched', 'skipped'):
          sync_log.records_updated += 1
      elif created:
          sync_log.records_created += 1
```

---

## 6. Conflict and Review Queue

Cases that require human review instead of auto-merge:

| Situation | Action |
|---|---|
| `match_confidence = 'low'` | Set `race_status = 'pending_review'` |
| `CandidateMatcher` returns `ambiguous` | Log to `SyncLog.last_error`; do not enrich |
| FEC creates a new Race stub (no Civic equivalent) | `match_confidence = 'medium'`, `race_status = 'pending_review'` |
| Enrichment source has different party/incumbent value than primary | Log discrepancy in `source_metadata`; keep primary source value |

Admin staff can review the `pending_review` queue in the Django admin and either approve/merge or reject.

---

## 7. Orchestration and the Existing Civic Flow

The existing Civic tasks (`sync_elections`, `sync_election_races`) are **not changed** in this plan. They continue to write directly to `Election`, `Race`, and `Candidate` via `update_or_create` with `canonical_key`.

The orchestrator is introduced as a **new write path for non-Civic sources**. A future refactor could route Civic writes through the orchestrator too, but that is out of scope for this plan.

---

## Next Document

[05-scheduling.md](05-scheduling.md) — Celery beat task schedule and rate-limit strategy.
