# Ohio Election Results — Research Notes

**Site:** https://www.ohiosos.gov/elections/election-results-and-data/
**Data Dashboard:** https://www.ohiosos.gov/elections/voters/ohio-election-results-data/
**DATA Act Portal:** https://data.ohiosos.gov/voter
**Live Results:** https://liveresults.ohiosos.gov
**Operated by:** Ohio Secretary of State
**Researched:** March 4, 2026
**Status:** Public, no authentication required

---

## Overview

Ohio has one of the most advanced election data transparency systems in the nation, anchored by the first-in-the-nation **Data Analysis Transparency Archive (DATA) Act** passed in 2023. The Office of Data Analytics and Archives provides detailed data tools for absentee/early voting trends, historical results, voter registration, and daily voter roll snapshots.

---

## Data Access

### Election Results Data Dashboard
- Custom-built interactive dashboard
- County-level data from 88 county boards since 2016 Primary
- Updated after official certification
- Best on desktop

### Live Election Night Results
- **URL:** https://liveresults.ohiosos.gov
- Real-time unofficial results on election night

### Official Election Results (XLSX Downloads)
- Summary-level and precinct-level results as XLSX files
- Organized by race and party
- Includes voter registration and turnout data
- Available for each election cycle

### DATA Act — Daily Voter Registration Snapshots
- **URL:** https://data.ohiosos.gov/voter
- Daily snapshots of voter registration database from all 88 counties
- Search by date and county
- Raw, unmodified data as transmitted by county boards
- 60,000+ county files, several terabytes total
- Bulk download available for large searches
- Contact: data@ohiosos.gov

### Election Results Data Dashboard (Additional)
- Absentee/early voting tracking tools
- Historical election results analysis

---

## API Access

No traditional REST API, but the DATA Act portal provides:
1. Searchable file access for daily voter registration snapshots
2. Bulk download capability
3. XLSX downloads for all official election results

---

## Notes

- 88 county boards of elections (fully decentralized system)
- DATA Act (2023) is landmark transparency legislation
- Daily voter registration snapshots created at 4 PM, transmitted by 11:59 PM
- Ohio is one of 8 states with fully decentralized election administration
- Precinct-level data available as XLSX
- 8+ million voter records in system
