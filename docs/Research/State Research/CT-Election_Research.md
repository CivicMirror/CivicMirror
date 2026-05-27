# Connecticut Election Results — Research Notes

**Site:** https://portal.ct.gov/SOTS/Election-Services/Election-Results/Election-Results
**Historical Database:** https://electionhistory.ct.gov/eng
**EMS Public Reporting:** https://ctemspublic.pcctg.net
**Open Data Portal:** https://data.ct.gov/Government/Election-Results-and-Voter-Turnout/2cta-kxuv
**Operated by:** Connecticut Secretary of the State
**Researched:** March 4, 2026
**Status:** Public, no authentication required

---

## Overview

Connecticut provides election results through multiple channels: a historical elections database (1787–present), an Elections Management System for recent real-time results, and the CT Open Data Portal with structured datasets.

---

## Data Access

### Historical Elections Database
- **URL:** https://electionhistory.ct.gov/eng
- Coverage: State elections from 1787 to present; municipal elections from 2001 to present
- Searchable by contests, questions, candidates

### Elections Management System (EMS)
- **URL:** https://ctemspublic.pcctg.net (August 2018 to present)
- Real-time election night reporting
- Town-by-town results

### CT Open Data Portal
- **URL:** https://data.ct.gov/Government/Election-Results-and-Voter-Turnout/2cta-kxuv
- Structured dataset with API access via Socrata/SODA
- Voter turnout and results data
- Available in CSV, JSON, and other formats through the portal API

### Statement of Vote Archive
- PDF documents from 1922 to present (General Election results)
- Available through Secretary of the State's website

---

## API Access

- **Socrata/SODA API** via CT Open Data Portal for structured data queries
- No dedicated SOS REST API identified
- Historical database is HTML-based, no API

---

## Notes

- The CT Open Data Portal (data.ct.gov) provides the most programmatic-friendly access via Socrata API
- Historical depth is exceptional (1787–present)
- EMS system used for all elections since August 2018
- Municipal results available from 2001 onward in the historical database
