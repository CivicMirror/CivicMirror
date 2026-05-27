# California Election Results — Research Notes

**API Base URL:** https://api.sos.ca.gov  
**Results Site:** https://electionresults.sos.ca.gov/  
**Media Files:** https://media.sos.ca.gov/  
**Operated by:** California Secretary of State  
**Researched:** March 4, 2026  
**Status:** Public, no authentication required

---

## Overview

California operates one of the most comprehensive public election data systems in the country. The Secretary of State provides a **full REST API** (Election Night Reporting REST API v2) that returns JSON by default with optional CSV output. Additionally, structured ASCII flat files and bulk download files are available through a media portal.

---

## REST API (Primary Programmatic Access)

### Base URL
```
https://api.sos.ca.gov
```

All access is over HTTPS. No authentication required for public access. Data returned as JSON by default; append `?f=csv` for CSV output.

### GET Request Endpoints

Endpoints map to URLs on ElectionResults.sos.ca.gov. Examples:

| Endpoint | Data Returned |
|----------|---------------|
| `/returns/governor` | Statewide results for Governor contest |
| `/returns/governor/county/lake` | Lake County results for Governor |
| `/returns/ballot-measures` | Statewide ballot measure results |
| `/returns/ballot-measures/county/alameda` | Alameda County ballot measure results |
| `/returns/us-senate` | Statewide U.S. Senate results |
| `/returns/status` | County reporting status |

### Query Endpoint (POST/GET)
```
GET /returns/query?r=["RaceId1","RaceId2"]
```

- RaceIds passed as JSON array via parameter `r`
- Maximum 10 RaceIds per request (500 error if exceeded)
- CSV format not supported for query endpoint
- Contest IDs defined in API documentation appendix

**Example:**
```
https://api.sos.ca.gov/returns/query?r=["02000000000059"]
→ Statewide Governor results

https://api.sos.ca.gov/returns/query?r=["02000000000017"]
→ Lake County Governor results
```

### JSON Response Structure
```json
[
  {
    "raceTitle": "Governor - Statewide Results",
    "Reporting": "100.0% (27,188 of 27,188) precincts reporting",
    "ReportingTime": "December 12, 2025, 2:59 p.m.",
    "candidates": [
      {
        "Name": "Candidate Name",
        "Party": "Dem",
        "Votes": "1234567",
        "Percent": "55.2",
        "incumbent": true
      }
    ]
  }
]
```

---

## Media / Flat Files

### ASCII Files (per election)
Available at `https://media.sos.ca.gov/media/`:

| File | Description |
|------|-------------|
| `C[YY][EL].txt` | Candidate information |
| `P[YY][EL].txt` | Precinct numbers by county |
| `R[YY][EL].txt` | Contest codes and descriptions |
| `S[YY][EL].txt` | County codes and names |
| `V[YY][EL].txt` | Voting results |

File naming: `[YY]` = 2-digit year, `[EL]` = election type code (e.g., `SS` for Special Statewide).
Example: `C25SS.txt` = Candidate info for 2025 Statewide Special.

### Supplementary Files
- `json-endpoints.csv` — Complete list of JSON endpoint URLs
- `api-endpoints.csv` — Complete list of API endpoint URLs
- `bulk-file-locations.xlsx` — Bulk file download locations

---

## API Documentation

Official documentation available as PDF:
- https://cms.cdn.sos.ca.gov/media/3-api-documentation-v19.pdf (latest version observed)
- Versioned documentation (v4, v5, v19, etc.) available for different elections

---

## Historical Data

- Statewide election results archived from 1996 to present on SOS website
- Historical voter registration and participation statistics from 1910–present (PDF)
- Prior elections accessible at https://www.sos.ca.gov/elections/prior-elections/statewide-election-results
- CEDA (California Elections Data Archive) provides local election results for counties, cities, and school districts from 1995–present

---

## Notes

- API endpoints change per election cycle (new contest IDs each election)
- The `json-endpoints.csv` and `api-endpoints.csv` files provide the definitive list of available endpoints for each election
- County-level results available; precinct data available through flat files
- SOS only certifies state and federal contests; local results via county elections offices
- Campaign finance data available separately through CAL-ACCESS at https://cal-access.sos.ca.gov/
