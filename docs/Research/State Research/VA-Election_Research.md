# Virginia Election Results — Research Notes

**Site:** https://www.elections.virginia.gov/resultsreports/election-results/
**Historical Database:** https://historical.elections.virginia.gov/
**Academic Database:** https://vavh.electionstats.com/
**Operated by:** Virginia Department of Elections (ELECT)
**Researched:** March 4, 2026
**Status:** Public, no authentication required

---

## Overview

Virginia has one of the more comprehensive election data systems in the nation. The Department of Elections provides JSON data files, CSV downloads, a searchable historical database, and GIS/map data. Results are available in multiple formats with both current and historical data access.

---

## Data Access

### Current Election Results
- **URL:** https://www.elections.virginia.gov/resultsreports/election-results/
- Results from 2005 to present
- Available as JSON files on the site
- Downloadable reports for changes to results after initial entry
- Updated in real-time during election night

### Individual Election Results CSV
- CSV download for 2005-present
- Precinct-level data

### Historical Elections Database
- **URL:** https://historical.elections.virginia.gov/
- Searchable database from 1789-present
- All from official source documents
- Inventory table showing which contests are available

### GIS/Map Data
- 2012-2018 election results available as zipped file geodatabase
- For desktop GIS users

### Virginia Public Access Project (VPAP)
- **URL:** https://www.vpap.org/
- Nonpartisan third-party data resource
- Campaign finance, election results, and political data
- Free, nonprofit

### Virginia Elections & State Elected Officials Database Project
- **URL:** https://vavh.electionstats.com/
- Academic database (UVA)
- General Assembly elections since 1949
- Gubernatorial results since 1851
- U.S. Senate elections since 1916
- U.S. House results since 1789
- Includes biographical data for ~10,000 individuals

### Voter Registration Data
- Available through Client Services
- Requires eligibility verification
- Comma-delimited text files
- Includes voter list, voting history, absentee data

---

## API Access

- **JSON data files** available directly on election results pages
- No dedicated REST API, but JSON files provide programmatic-friendly access
- CSV bulk downloads for historical data

---

## Notes

- 133 localities (95 counties + 38 independent cities)
- State Board of Elections certifies statewide results
- Local Electoral Boards certify locality results
- Odd-year election state (governor, legislature in odd years)
- Rich historical data going back to 1789
- VPAP provides excellent third-party data analysis
