# Hawaii Election Results — Research Notes

**Site:** https://elections.hawaii.gov/election-results/
**Open Data:** https://opendata.hawaii.gov/
**Operated by:** Hawaii Office of Elections
**Researched:** March 4, 2026
**Status:** Public, no authentication required

---

## Overview

Hawaii provides election results through the Office of Elections website with both PDF certified reports and text file downloads. Additionally, some election data is available on the Hawaii Open Data portal in multiple formats (CSV, JSON, XML, RDF).

---

## Data Access

### Election Results Portal
- **URL:** https://elections.hawaii.gov/election-results/
- Coverage: 1992–2024 (Primary and General elections)
- Results released in batches on election night (typically 3 runs)

### Certified Reports (PDF)
- Statewide Summary, County Summaries (Hawaii, Maui, Kauai, Honolulu)
- Statewide Precinct Detail
- Statement of Vote

### Certified Text Files
- Statewide Summary (text format)
- Statewide Precinct Detail (text format)
- Downloadable for programmatic processing

### Hawaii Open Data Portal
- **URL:** https://opendata.hawaii.gov/
- Election results datasets available in CSV, JSON, XML, RDF formats
- Example: General Election 2012 Results dataset

### Registration and Turnout Statistics
- Available through the Office of Elections website

---

## API Access

- **Hawaii Open Data Portal** provides API access via CKAN for datasets published there
- No dedicated SOS REST API identified
- Text file downloads provide the most reliable programmatic access

---

## Notes

- Results published in batch runs on election night (Run 1 ~7pm, Run 2 ~10pm, Run 3 next day)
- Four counties: Hawaii, Maui, Kauai, City & County of Honolulu
- Historical coverage from 1992 to present
- Contact: elections@hawaii.gov / (808) 453-8683
