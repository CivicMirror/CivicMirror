# Arizona Election Results — Research Notes

**Site:** https://azsos.gov/elections  
**Results Site:** https://results.arizona.vote/  
**Operated by:** Arizona Secretary of State  
**Researched:** March 4, 2026  
**Status:** Public, no authentication required

---

## Overview

Arizona provides election results through the Secretary of State's website with a notable **XML/FTP data feed** for media and programmatic access. This is one of the more developer-friendly state systems, offering structured real-time data during election night.

---

## Data Access

### XML/FTP Data Feed (Key Feature)
- **FTP Location:** `ftp://ftp.azsos.gov/ElectionResults/[year]/State/[election]/Results.Summary.xml`
- Media access to real-time XML files via FTP/HTTPS
- **SUMMARY level:** Vote counts aggregated by county and statewide
- **PRECINCT DETAIL:** Contest/choice at precinct level (FTP only)
- Updates in real time on election night (no more than once per 2 minutes)
- Press feed page: https://azsos.gov/pressazsosgov

### Results Website
- **URL:** https://results.arizona.vote/
- Interactive results display
- County-level results redirect to individual county websites

### Historical Results
- Available through the Secretary of State's website
- Organized by election year

---

## API Access

**XML data feed via FTP/HTTPS** — the primary programmatic access method:
- Real-time updates during election night
- Structured XML format
- Summary and precinct-level detail available
- No authentication required for FTP access

No REST API identified, but the XML feed provides equivalent functionality for results data.

---

## Notes

- Arizona's XML/FTP feed is notably more structured than most states
- County-level detail requires visiting individual county websites for some data
- The FTP feed is the recommended approach for programmatic access
- Update frequency capped at once per 2 minutes during election night
