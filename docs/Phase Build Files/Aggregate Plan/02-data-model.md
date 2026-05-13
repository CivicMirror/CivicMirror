# Data Model Changes — Multi-Source Aggregation

> **Status: ✅ IMPLEMENTED** — All model changes applied. Migrations: `elections/0003_*`, `ops/0002_*`, `ops/0003_synclog_notes`.

## Overview

The existing `elections` and `results` apps have a solid foundation. This plan calls for targeted additions to support multi-source enrichment, provenance tracking, and district normalization. The goal is **no breaking changes** to existing model behavior.

---

## 1. Additions to `Race` Model

### 1a. `source_metadata` JSONField

Store per-source reference IDs and sync state without requiring new columns for every source:

```python
# elections/models.py — add to Race
source_metadata = models.JSONField(default=dict, blank=True)
```

**Stored structure:**
```json
{
  "fec": {
    "election_id": "2024_H3CA05",
    "cycle": 2024,
    "last_synced": "2024-09-15T02:00:00Z"
  },
  "openstates": {
    "jurisdiction_id": "ocd-jurisdiction/country:us/state:ca/government",
    "last_synced": "2024-09-15T02:00:00Z"
  }
}
```

### 1b. `match_confidence` CharField

Flag the confidence level of cross-source identity matching:

```python
class MatchConfidence(models.TextChoices):
    VERIFIED = 'verified', 'Verified'       # OCD-ID exact match
    HIGH = 'high', 'High'                   # OCD + title match
    MEDIUM = 'medium', 'Medium'             # district + fuzzy title
    LOW = 'low', 'Low'                      # name-only match
    FLAGGED = 'flagged', 'Flagged for Review'

match_confidence = models.CharField(
    max_length=20,
    choices=MatchConfidence.choices,
    default=MatchConfidence.VERIFIED,
    blank=True,
)
```

---

## 2. Additions to `Candidate` Model

### 2a. External identifier fields

Add external source IDs as first-class fields (instead of burying them in JSON) for indexable lookups:

```python
# elections/models.py — add to Candidate
fec_candidate_id = models.CharField(max_length=20, blank=True, db_index=True)
bioguide_id = models.CharField(max_length=20, blank=True, db_index=True)
openstates_person_id = models.CharField(max_length=50, blank=True)
```

### 2b. `source_metadata` JSONField

Per-source enrichment data that doesn't need its own column:

```python
source_metadata = models.JSONField(default=dict, blank=True)
```

**Example:**
```json
{
  "congress": {
    "bioguide_id": "P000197",
    "official_full": "Nancy Pelosi",
    "phone": "202-225-4965",
    "office": "1236 Longworth House Office Building",
    "twitter": "SpeakerPelosi",
    "facebook": "NancyPelosi",
    "last_synced": "2024-09-15T02:00:00Z"
  },
  "fec": {
    "candidate_id": "H0CA08028",
    "committee_id": "C00117747",
    "last_synced": "2024-09-15T02:00:00Z"
  }
}
```

### 2c. `contact_phone` and `contact_office` CharField

Concrete fields for contact data that the frontend may display:

```python
contact_phone = models.CharField(max_length=30, blank=True)
contact_office = models.CharField(max_length=255, blank=True)
```

---

## 3. New Model: `SourceRecord`

A raw-payload store for auditability and replay. One record per (source, external_id) combination.

```python
# ops/models.py (add) or new app: integrations/models.py
class SourceRecord(models.Model):
    class SourceType(models.TextChoices):
        CIVIC = 'civic', 'Google Civic'
        FEC = 'fec', 'OpenFEC'
        CONGRESS = 'congress', 'Congress Legislators'
        OPENSTATES = 'openstates', 'Open States'
        CENSUS = 'census', 'U.S. Census'
        OPENELECTIONS = 'openelections', 'OpenElections'
        MEDSL = 'medsl', 'MEDSL'

    source = models.CharField(max_length=30, choices=SourceType.choices)
    external_id = models.CharField(max_length=255)
    raw_payload = models.JSONField()
    payload_checksum = models.CharField(max_length=64)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    linked_race = models.ForeignKey('elections.Race', null=True, blank=True, on_delete=models.SET_NULL, related_name='source_records')
    linked_candidate = models.ForeignKey('elections.Candidate', null=True, blank=True, on_delete=models.SET_NULL, related_name='source_records')

    class Meta:
        unique_together = [('source', 'external_id')]
        indexes = [
            models.Index(fields=['source', 'external_id']),
            models.Index(fields=['linked_race']),
        ]
```

**Purpose:**
- Stores raw API payloads for debugging
- Checksum-based change detection for incremental syncs (skip unchanged records)
- Link to matched Race/Candidate for audit trail
- Allows replay if mapping logic changes

---

## 4. New Model: `DistrictRecord`

Cached district/jurisdiction resolution for addresses and ZIP codes.

```python
# integrations/census/models.py (or elections/models.py)
class DistrictRecord(models.Model):
    state = models.CharField(max_length=2)
    district_type = models.CharField(max_length=50)  # congressional, state_upper, state_lower, county, etc.
    district_number = models.CharField(max_length=20, blank=True)
    ocd_division_id = models.CharField(max_length=255, db_index=True)
    name = models.CharField(max_length=255)
    fips_code = models.CharField(max_length=20, blank=True)
    election_year_valid = models.IntegerField(null=True, blank=True)  # for redistricting awareness
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('ocd_division_id', 'election_year_valid')]
        indexes = [models.Index(fields=['state', 'district_type'])]
```

---

## 5. New Model: `ElectionCycle`

Federal elections are cycle-oriented (2-year cycles for House, 6-year for Senate). This prevents awkward mapping between FEC cycles and Civic election dates.

```python
# elections/models.py
class ElectionCycle(models.Model):
    cycle_year = models.IntegerField(unique=True)  # 2020, 2022, 2024...
    description = models.CharField(max_length=100, blank=True)  # "2024 Federal Midterm/Presidential"
    cycle_start = models.DateField()
    cycle_end = models.DateField()

    class Meta:
        ordering = ['-cycle_year']
```

Add optional FK to `Election`:
```python
# In Election model:
election_cycle = models.ForeignKey('ElectionCycle', null=True, blank=True, on_delete=models.SET_NULL, related_name='elections')
```

---

## 6. `Race.Source` Additions

Only **origin** sources (entities that create `Race` records) are added. Enrichment sources are not listed here.

```python
class Source(models.TextChoices):
    CIVIC_API = 'civic_api', 'Civic API'        # EXISTING
    COMMUNITY = 'community', 'Community'         # EXISTING
    OPENELECTIONS = 'openelections', 'OpenElections'   # NEW — historical only
    MEDSL = 'medsl', 'MEDSL'                     # NEW — historical only
```

FEC, OpenStates, and congress-legislators are **not** listed as Race sources because they do not create primary race records.

---

## 7. `SyncLog` Additions

Add a `cycle_year` field to allow filtering sync logs by federal election cycle:

```python
# ops/models.py
cycle_year = models.IntegerField(null=True, blank=True)
records_skipped = models.IntegerField(default=0)  # unchanged/checksum-matched records
```

---

## 8. Summary of Required Django Migrations

| Migration | App | Change |
|---|---|---|
| Add `Race.source_metadata` | elections | New JSONField |
| Add `Race.match_confidence` | elections | New CharField with choices |
| Add `Candidate.fec_candidate_id` | elections | New CharField, indexed |
| Add `Candidate.bioguide_id` | elections | New CharField, indexed |
| Add `Candidate.openstates_person_id` | elections | New CharField |
| Add `Candidate.source_metadata` | elections | New JSONField |
| Add `Candidate.contact_phone` | elections | New CharField |
| Add `Candidate.contact_office` | elections | New CharField |
| Add `Race.Source.OPENELECTIONS` + `MEDSL` | elections | Choices extension |
| Create `SourceRecord` | ops or integrations | New model |
| Create `DistrictRecord` | elections or integrations | New model |
| Create `ElectionCycle` | elections | New model |
| Add `Election.election_cycle` FK | elections | New nullable FK |
| Add `SyncLog.cycle_year` | ops | New IntegerField |
| Add `SyncLog.records_skipped` | ops | New IntegerField |

---

## What Is NOT Changing

- `Race.source` = `civic_api` for all Civic-sourced races (unchanged semantics)
- `Race.canonical_key` construction for Civic races (unchanged)
- `Candidate` unique constraint on `(race, name)` — remains, but the orchestrator will manage duplicates before they reach this constraint
- Community race flow, serializers, and frontend API contract — all unchanged

---

## Next Document

[03-source-adapters.md](03-source-adapters.md) — Per-source adapter specifications.
