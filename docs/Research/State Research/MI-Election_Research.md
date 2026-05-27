# Michigan Election Results — Research Notes

**Site:** https://www.michigan.gov/sos/elections/election-results-and-data
**Third-Party API:** https://michiganelections.io/
**Voting Dashboard:** https://www.michigan.gov/sos/elections/election-results-and-data/voter-participation-dashboard
**Operated by:** Michigan Secretary of State / Bureau of Elections
**Researched:** March 4, 2026
**Status:** Public, no authentication required

---

## Overview

Michigan provides election results through the Secretary of State's website with searchable data tables, a Voting Dashboard, and county-level results. Additionally, a third-party API (michiganelections.io) built by Citizen Labs provides programmatic access to voter registration, ballot, and election data.

---

## Data Access

### State Election Results & Data
- **URL:** https://www.michigan.gov/sos/elections/election-results-and-data
- Searchable table by year, results/data type, report type
- Historical data through State of Michigan Archives
- Local election data via county websites (83 counties)

### Michigan Voting Dashboard
- Daily updates starting 45 days before elections
- Absentee/early voting tracking
- Voter history data from Qualified Voter File (QVF)
- Stops updating 30 days after Election Day

### County-Level Results
- Links to all 83 county election websites
- Unofficial results posted on election night

### Third-Party API: michiganelections.io
- **URL:** https://michiganelections.io/api/
- **Documentation:** https://michiganelections.io/docs/ (Swagger UI)
- Open-source: https://github.com/citizenlabsgr/elections-api/
- Endpoints: registrations, elections, positions, proposals
- JSON API with versioned content negotiation
- Zapier integration available
- **Not official state API** — community-built by Citizen Labs

### Campaign Finance
- Searchable database for campaign finance data

---

## API Access

- **Official:** No state-operated REST API
- **Third-Party:** michiganelections.io provides REST API (voter registration status, ballot info, elections)
- Contact: Elections@Michigan.gov

---

## Notes

- 83 counties, 1,500+ election clerks statewide
- Qualified Voter File (QVF) is the central voter database
- Board of State Canvassers certifies results
- Paper ballot / optical scan system statewide
- Member of ERIC (Electronic Registration Information Center)
