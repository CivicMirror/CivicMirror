# Delaware Election Results — Research Notes

**Site:** https://elections.delaware.gov/results/
**Archive:** https://elections.delaware.gov/elections/election_archive.shtml
**Operated by:** Delaware Department of Elections / State Election Commissioner
**Researched:** March 4, 2026
**Status:** Public, no authentication required

---

## Overview

Delaware provides election results through the Department of Elections website with CSV download capability and multiple result view options including statewide, by district, by election district, by county, and by county with Wilmington breakdown.

---

## Data Access

### Current Election Results
- **URL:** https://elections.delaware.gov/results/html/index.shtml?electionId=GE2024
- View modes: Statewide, By District, By Election District, By County, By County W/ Wilmington
- **CSV Download:** "Download CSV Report" button available on results pages
- Select individual races or full report

### Results Archive
- **URL:** https://elections.delaware.gov/elections/election_archive.shtml
- Coverage: 1940–2025 (select years)
- Year selector dropdown for historical results

### Election ID Format
- URL parameter format: `electionId=GE2024` (General Election 2024), `PR2024` (Primary 2024)

### Voter Registration Data
- Available for purchase through formal order process
- Free for filed/nominated candidates

---

## API Access

No public REST API identified. Data access is through:
1. CSV downloads from results pages
2. HTML results pages with multiple view modes
3. Historical archive by year
4. Voter registration data via formal order

---

## Notes

- CSV download is the primary programmatic data access method
- Results can be filtered by race, district, county
- Archive goes back to 1940 with increasing detail in modern elections
- Three counties only (New Castle, Kent, Sussex) simplifies geographic data
