# North Carolina Election Results — Research Notes

**Site:** https://www.ncsbe.gov/results-data
**Election Results:** https://www.ncsbe.gov/results-data/election-results
**Historical Data:** https://www.ncsbe.gov/results-data/election-results/historical-election-results-data
**How to Work with Data:** https://www.ncsbe.gov/about-elections/county-boards-elections/county-resources/county-board-kit/how-work-our-data
**Operated by:** North Carolina State Board of Elections
**Researched:** March 4, 2026
**Status:** Public, no authentication required

---

## Overview

North Carolina offers one of the most comprehensive public election data systems in the country. The NC State Board of Elections proudly states they "offer more publicly available election data than almost any other state." Data includes election results, voter registration, voter history, absentee/provisional data, and GIS files, all available through their website and a public FTP site.

---

## Data Access

### Election Results Dashboard
- Live results updated every 5–10 minutes on election night
- Interactive maps, tables, and charts
- Downloadable spreadsheets
- Historical results from 1992–present

### Historical Election Results Data
- **URL:** https://www.ncsbe.gov/results-data/election-results/historical-election-results-data
- Federal, state, and local results for 20+ years
- Precinct-sorted data (with statistical noise for ballot secrecy)
- Certified results as PDF

### Public FTP Site
- Direct access to all public data files
- Voter registration data (updated weekly, Saturdays)
- Voter history data (individual-level, linkable via NCID)
- Election results files
- Absentee and provisional data

### Voter Registration Data
- **URL:** https://www.ncsbe.gov/results-data/voter-registration-data
- Current voter-level registration records
- 15+ years of historical snapshots
- Linkable to voter history via NCID or county + voter_reg_num
- Weekly Saturday updates
- Demographics: party affiliation, race, ethnicity, gender, age

### Voter History Data
- **URL:** https://www.ncsbe.gov/results-data/voter-history-data
- Individual voter participation records (10+ years)
- Group-level demographic counts (20+ years)
- Statewide and county-level files
- Includes voting method, county, precinct

### Absentee & Provisional Data
- Absentee ballot tracking files
- Provisional ballot data
- Same-day registration data

---

## API Access

No formal REST API, but the **public FTP site** provides bulk data downloads equivalent to API access. Files are well-documented with layout files and detailed instructions.

---

## Notes

- 100 counties
- Exceptionally well-documented data with "How to Work with Our Data" guide
- Precinct-sorted results include statistical noise to protect ballot secrecy
- Voter history files linkable to registration files for comprehensive analysis
- Data files updated weekly (Saturdays) for voter registration and history
- One of the best state election data systems nationwide
