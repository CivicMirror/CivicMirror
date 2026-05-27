# WV Official Results Adapter — Implementation Plan

## Background
WV races show "Results pending" indefinitely because:
1. No WV results adapter exists in `backend/results/adapters/`
2. The `ingest_official_results` Celery task has no beat schedule — it is never triggered automatically

## Data Source Discovery
Initial research targeted the WV SOS ASP.NET portal (`apps.sos.wv.gov/elections/results/`),
but the actual production results portal linked from `sos.wv.gov/elections` is a
**Clarity Elections** instance operated by SOE Software / ES&S:

- **WV 2026 Primary summary**: https://results.enr.clarityelections.com/WV/126209/web.345435/#/summary
- **Party sub-pages**: `#/summary?category=C_1` (Republican), `C_2` (Democrat), `C_3` (Non-Partisan)
- **Race detail example**: https://results.enr.clarityelections.com/WV/126209/web.345435/#/detail/12350
- **XML download**: https://results.enr.clarityelections.com/WV/126209/371599/reports/detailxml.zip

The `371599` segment is the **current version ID** — it increments as results are updated.

## The `clarify` Library
OpenElections maintains a Python library purpose-built for Clarity Elections:
- **Repo**: https://github.com/openelections/clarify
- **Install**: `pip install clarify`
- **Python support**: 3.8–3.12 (MIT license)

### Key classes

```python
import clarify

# Discover the current version and XML URL automatically
j = clarify.Jurisdiction(
    url='https://results.enr.clarityelections.com/WV/126209/web.345435/',
    level='state'
)
xml_url = j.report_url('xml')
# → https://results.enr.clarityelections.com/WV/126209/371599/reports/detailxml.zip

# Parse the XML
p = clarify.Parser()
p.parse_zip('/tmp/detailxml.zip')

for contest in p.contests:
    print(contest.text)          # "JUSTICE OF SUPREME COURT OF APPEALS"
    print(contest.is_question)   # False = candidate race, True = ballot measure
    for choice in contest.choices:
        print(choice.text, choice.total_votes)
```

### What the XML contains
- `contest.text` — office/race title (used to match CivicMirror `Race.office_title`)
- `contest.is_question` — `True` for ballot measures/referendums, `False` for candidate races
- `contest.precincts_reporting` / `contest.precincts_participating` — reporting progress
- `contest.choices` — list of candidates or Yes/No options
- `choice.text` — candidate name or option label
- `choice.total_votes` — statewide vote total
- `p.timestamp` — datetime of last update
- `p.election_name` — e.g. "2026 West Virginia Primary Election"

## Implementation Plan

### Files to Create
| File | Purpose |
|------|---------|
| `backend/results/adapters/clarity.py` | Generic Clarity adapter (works for any state) |
| `backend/results/adapters/wv.py` | WV adapter — 5 lines, just `@register` + `state='WV'` |
| `backend/results/tests/test_clarity_adapter.py` | Unit tests with XML fixture |

### Files to Modify
| File | Change |
|------|--------|
| `backend/requirements/base.txt` | Add `clarify`, `lxml`, `python-dateutil` |
| `backend/elections/models.py` | Add `results_url = models.URLField(null=True, blank=True)` to `Election` |
| `backend/elections/admin.py` | Expose `results_url` in `ElectionAdmin` |
| `backend/results/adapters/base.py` | Add `office_title: Optional[str] = None` to `ResultRow` |
| `backend/results/tasks.py` | Add `poll_pending_results` task; update `_process_race_results` to filter by `office_title` |
| `backend/config/celery.py` | Add `poll-pending-election-results` beat entry (daily 06:00 UTC) |
| `backend/elections/migrations/` | New migration for `results_url` field |

## Data Flow

```
Admin sets Election.results_url
  → clarify.Jurisdiction(results_url, level='state')
  → fetches current_ver.txt → gets version ID (e.g. 371599)
  → constructs https://.../371599/reports/detailxml.zip
  → downloads + unzips → detail.xml
  → clarify.Parser.parse_zip()
  → for each Contest:
      ResultRow(
          office_title = contest.text,
          candidate_name = choice.text  (if not is_question)
          option_label = choice.text    (if is_question)
          vote_count = choice.total_votes,
          result_type = UNOFFICIAL (until 100% precincts)
      )
  → ingest_official_results task
  → OfficialResult rows upserted
  → Race.certification_status updated
```

## `results_url` Field Strategy
The `results_url` is set **manually by an admin** in the Django admin panel.
This is intentional: it keeps the mapping auditable and doesn't require
auto-discovery logic that could break with WV SOS website changes.

For the WV 2026 Primary:
```
results_url = https://results.enr.clarityelections.com/WV/126209/web.345435/
```

## office_title Matching
The Clarity `contest.text` values for WV will look like:
- `"JUSTICE OF SUPREME COURT OF APPEALS (UNEXPIRED TERM) - DIVISION 2"`
- `"U.S. SENATE"`
- `"U.S. HOUSE OF REPRESENTATIVES - DISTRICT 1"`

CivicMirror `Race.office_title` values come from the Google Civic Info API and
may differ in capitalization or exact wording. The matching in `_process_race_results`
should:
1. Pre-filter rows to those whose `office_title` matches `race.office_title` (case-insensitive)
2. Fall back to checking all rows if no `office_title` match found (graceful degradation)

## result_type Logic
| Condition | result_type |
|-----------|------------|
| Precincts reporting < 100% | `UNOFFICIAL` |
| Precincts reporting = 100% | `UNOFFICIAL` (still unofficial until certified) |
| Officially certified by WV SOS | `OFFICIAL` (manual admin action or future hook) |

For now, all Clarity results are ingested as `UNOFFICIAL`. The `Race.certification_status`
tracks the overall state; individual `OfficialResult.result_type` reflects the Clarity data.

## Auto-Polling Beat Task
A new `poll_pending_results` Celery task runs **daily at 06:00 UTC**:

```python
@shared_task
def poll_pending_results():
    from elections.models import Election, Race
    from results.adapters.registry import list_supported_states

    supported = set(list_supported_states())
    elections = Election.objects.filter(
        election_date__lt=timezone.now().date(),
        status=Election.Status.RESULTS_PENDING,
        state__in=supported,
    )
    for election in elections:
        ingest_official_results.delay(election.state, election.pk)
```

This means once WV posts results, the next 06:00 UTC run will automatically pick them up.

## Multi-State Potential
The `ClarityAdapter` base class is state-agnostic. Any state using Clarity Elections
can get results by:
1. Creating a 5-line adapter file
2. Setting `results_url` on their election records in the admin

States known to use Clarity Elections include: WV, GA, AR, KY, IA, and many others.

## Deep API Research Findings (confirmed via live probing)

### Critical: `web.{hash}` is NOT the data version
The `web.345435` segment in the browser URL is the **Angular SPA bundle version** (UI only).
The actual data API version comes from `current_ver.txt`:
```
GET https://results.enr.clarityelections.com/WV/126209/current_ver.txt
→ 371599
```
All data endpoints use this numeric version, **not** the web hash.

### JSON API (simpler than XML zip)
`summary.json` contains all statewide results in a single JSON response — no ZIP download needed:

```
GET /WV/126209/371599/json/en/summary.json
```

Each contest object in the array:
```json
{
  "C": "U.S. SENATOR - REP",     // contest name
  "K": "100",                     // race key (matches #/detail/K in browser URL)
  "CATKEY": "C_1",                // C_1=Republican, C_2=Democrat, C_3=Non-Partisan
  "PR": 51,                       // precincts reporting
  "TP": 55,                       // total precincts
  "CH": ["SHELLEY MOORE CAPITO", "TOM WILLIS", ...],  // candidate names
  "P":  ["REP", "REP", ...],      // parties
  "V":  [80032, 22736, ...],      // votes per candidate
  "PCT":[66.49, 18.89, ...],      // percentage per candidate
  "W":  [0, 0, ...],              // winner flags (1=winner)
  "T":  120357                    // total votes cast
}
```

This is **preferred over the XML zip** for our use case — no download/unzip, already has winner flags.

### Live WV 2026 Primary Data (as of 2026-05-17, 51/55 precincts)
| Candidate | Party | Votes | % |
|-----------|-------|-------|---|
| SHELLEY MOORE CAPITO | REP | 80,032 | 66.5% |
| TOM WILLIS | REP | 22,736 | 18.9% |
| BRYAN McKINNEY | REP | 5,556 | 4.6% |
| DAVID PURKEY | REP | 5,014 | 4.2% |

### Reference Implementation
`move-coop/parsons` (`parsons/scytl/scytl.py`) is an excellent reference — it uses `current_ver.txt`
+ `summary.json` (or `detailxml.zip` for county-level) with version-change detection for efficient polling.

### States Using Clarity Elections
| State | Status |
|-------|--------|
| WV, CO, IA, SC | ✅ Accessible (ENR Web 4.x) |
| FL, OK, AL | ✅ Accessible (ENR Web 2.x, older format) |
| GA, AR, KY, LA, NC, NJ, TX, PA, MO, IL | ⚠️ 403 (Clarity but IP/access restricted) |
| MT, SD, MS, VA, TN, NM, AK, IN | ❌ Not on Clarity |

States like CO, IA, SC can use the same generic adapter once `results_url` is set in admin.

### Updated Adapter Strategy
Use the **JSON API** (`summary.json`) instead of downloading `detailxml.zip`:
1. `GET /WV/126209/current_ver.txt` → version (`371599`)
2. `GET /WV/126209/371599/json/en/summary.json` → all contest results
3. For each contest object: create `ResultRow` entries
4. Cache the version number; only re-fetch data when version changes (efficient polling)

The `clarify` PyPI library is still valid (uses XML) but the JSON approach is lighter.

---

## Known Limitations
- WV 2026 Primary results are currently **unofficial and in progress** (counting ongoing as of 2026-05-17)
- Results will be returned as `UNOFFICIAL` until manually marked otherwise
- If WV changes their Clarity election ID (126209) for future elections, a new `results_url`
  must be set in the admin for each new election
- The `clarify` library requires network access to `results.enr.clarityelections.com`

## Todo Checklist
1. [ ] Add `clarify`, `lxml`, `python-dateutil` to `requirements/base.txt`
2. [ ] Add `results_url` to `Election` model + migration + admin
3. [ ] Add `office_title` to `ResultRow` in `base.py`
4. [ ] Update `_process_race_results` in `tasks.py` to filter by `office_title`
5. [ ] Create `backend/results/adapters/clarity.py` (generic ClarityAdapter)
6. [ ] Create `backend/results/adapters/wv.py` (WestVirginiaAdapter)
7. [ ] Add `poll_pending_results` task to `results/tasks.py`
8. [ ] Add beat schedule entry in `config/celery.py`
9. [ ] Write tests in `results/tests/test_clarity_adapter.py`
10. [ ] Post-deploy: set `results_url` in Django admin for WV 2026 Primary
