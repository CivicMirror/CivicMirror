# Alabama Election Results — Research Notes

**Site:** https://www.sos.alabama.gov/alabama-votes/voter/election-data  
**Election Night Results:** https://www2.alabamavotes.gov/electionnight/  
**Operated by:** Alabama Secretary of State  
**Researched:** March 4, 2026  
**Status:** Public, no authentication required

---

## Overview

Alabama provides election results through the Secretary of State's website with both election night reporting and historical certified results. The election night site includes an "Export Data" option. Certified results are available as downloadable Excel files.

---

## Data Access

### Election Night Results
- **URL:** https://www2.alabamavotes.gov/electionnight/
- Real-time results on election night with "Export Data" option
- Appears to be a web application with interactive display

### Historical / Certified Results
- **URL:** https://www.sos.alabama.gov/alabama-votes/voter/election-data
- Excel (.xls/.xlsx) files available for certified results
- Organized by election year and party (e.g., 2022 Republican Party Certification, 2022 Democratic Party Certification)
- Historical data available going back multiple election cycles

### Data Formats
- Excel files for certified results
- Export option on election night site (format TBD — likely CSV or Excel)

---

## API Access

No public REST API identified. Data access is through:
1. Manual download of Excel files from the election data page
2. Export function on election night results site
3. HTML scraping of results pages

---

## Notes

- Election night site and certified results are on different subdomains
- No programmatic API or structured data feed was identified
- Excel files require manual download or URL construction based on naming patterns
