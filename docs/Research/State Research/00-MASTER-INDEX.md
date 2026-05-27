# US State Election Results Data Access — Master Index

**Researched:** March 4, 2026
**Coverage:** 48 states (excludes TX and MA, which were pre-existing)
**Purpose:** Document official election results data access methods (APIs, CSV/Excel downloads, data feeds, web portals) for each state

---

## States by Data Access Sophistication

### Tier 1: Full REST APIs or Structured Data Feeds

| State | System | Access Method |
|-------|--------|---------------|
| **California** | Election Night Reporting REST API v2 | `https://api.sos.ca.gov` — JSON default, CSV via `?f=csv`, XML/FTP feeds |
| **Michigan** | michiganelections.io (third-party) | Community-built REST API by Citizen Labs (open-source) |
| **Arizona** | FTP Data Feed | `ftp://ftp.azsos.gov/ElectionResults/` — XML, real-time on election night |

### Tier 2: Open Data Portals with Socrata/SODA APIs

| State | Portal | Notes |
|-------|--------|-------|
| **Connecticut** | CT Open Data Portal | Socrata/SODA API; historical database from 1787 |
| **Pennsylvania** | PA Open Data Portal (`data.pa.gov`) | Socrata/SODA API; CSV/JSON downloads |

### Tier 3: JSON/CSV Data Files + Comprehensive Downloads

| State | Notable Features |
|-------|-----------------|
| **Virginia** | JSON data files on results pages; CSV bulk downloads 2005-present; GIS data; historical database 1789-present |
| **North Carolina** | Public FTP site; weekly data updates; election night dashboard every 5-10 min; historical data 1992-present |
| **Ohio** | DATA Act (2023) — daily voter registration snapshots from 88 counties; XLSX downloads; interactive dashboards |
| **Florida** | Election Watch with Excel/tab-delimited/pipe-delimited; precinct-level from 2012; data extract utility |
| **New York** | Flateau Act (effective April 2026) mandates comprehensive data; election district-level; 12-year retention |
| **Washington** | Extensive statistics downloads; ballot return stats; GIS precinct files; VoteWA system |

### Tier 4: Searchable Historical Databases

| State | Database | Coverage |
|-------|----------|----------|
| **Colorado** | Historical Election Data | 1902-present |
| **Connecticut** | CT Elections Database | 1787-present |
| **Vermont** | VT Elections Archive | Searchable historical database |
| **Virginia** | Historical Elections DB | 1789-present |
| **Illinois** | Vote Total Search | 1998-present |
| **Wisconsin** | WEC Results Archive | 10+ years; ward-by-ward XLSX |

### Tier 5: Standard Download Systems (Excel/PDF/CSV)

All remaining states provide web-based results portals with downloadable files (typically Excel, PDF, or CSV). No public REST APIs identified.

AL, AK, AR, DE, GA, HI, ID, IN, IA, KS, KY, LA, ME, MD, MN, MS, MO, MT, NE, NV, NH, NJ, NM, ND, OK, OR, RI, SC, SD, TN, UT, WV, WY

---

## Quick Reference: All 48 States

| Code | State | File | Key URL |
|------|-------|------|---------|
| AL | Alabama | AL-Election_Research.md | sos.alabama.gov/alabama-votes/voter/election-data |
| AK | Alaska | AK-Election_Research.md | elections.alaska.gov/results/ |
| AZ | Arizona | AZ-Election_Research.md | azsos.gov/elections (FTP feed) |
| AR | Arkansas | AR-Election_Research.md | sos.arkansas.gov/elections |
| CA | California | CA-Election_Research.md | api.sos.ca.gov (REST API) |
| CO | Colorado | CO-Election_Research.md | historicalelectiondata.coloradosos.gov |
| CT | Connecticut | CT-Election_Research.md | data.ct.gov (Socrata API) |
| DE | Delaware | DE-Election_Research.md | elections.delaware.gov |
| FL | Florida | FL-Election_Research.md | dos.myflorida.com/elections |
| GA | Georgia | GA-Election_Research.md | sos.ga.gov/elections |
| HI | Hawaii | HI-Election_Research.md | elections.hawaii.gov |
| ID | Idaho | ID-Election_Research.md | sos.idaho.gov/elections |
| IL | Illinois | IL-Election_Research.md | elections.il.gov |
| IN | Indiana | IN-Election_Research.md | indianavoters.in.gov |
| IA | Iowa | IA-Election_Research.md | sos.iowa.gov/elections |
| KS | Kansas | KS-Election_Research.md | sos.ks.gov/elections |
| KY | Kentucky | KY-Election_Research.md | elect.ky.gov |
| LA | Louisiana | LA-Election_Research.md | voterportal.sos.la.gov |
| ME | Maine | ME-Election_Research.md | maine.gov/sos/cec/elec |
| MD | Maryland | MD-Election_Research.md | elections.maryland.gov |
| MI | Michigan | MI-Election_Research.md | michiganelections.io (API) |
| MN | Minnesota | MN-Election_Research.md | sos.state.mn.us/elections |
| MS | Mississippi | MS-Election_Research.md | sos.ms.gov/elections |
| MO | Missouri | MO-Election_Research.md | sos.mo.gov/elections |
| MT | Montana | MT-Election_Research.md | sosmt.gov/elections |
| NE | Nebraska | NE-Election_Research.md | sos.nebraska.gov/elections |
| NV | Nevada | NV-Election_Research.md | nvsos.gov/elections |
| NH | New Hampshire | NH-Election_Research.md | sos.nh.gov/elections |
| NJ | New Jersey | NJ-Election_Research.md | nj.gov/state/elections |
| NM | New Mexico | NM-Election_Research.md | sos.nm.gov/voting-and-elections |
| NY | New York | NY-Election_Research.md | elections.ny.gov |
| NC | North Carolina | NC-Election_Research.md | ncsbe.gov (FTP site) |
| ND | North Dakota | ND-Election_Research.md | vote.nd.gov |
| OH | Ohio | OH-Election_Research.md | data.ohiosos.gov (DATA Act) |
| OK | Oklahoma | OK-Election_Research.md | oklahoma.gov/elections |
| OR | Oregon | OR-Election_Research.md | sos.oregon.gov/elections |
| PA | Pennsylvania | PA-Election_Research.md | data.pa.gov (Socrata API) |
| RI | Rhode Island | RI-Election_Research.md | elections.ri.gov |
| SC | South Carolina | SC-Election_Research.md | scvotes.gov |
| SD | South Dakota | SD-Election_Research.md | sdsos.gov/elections |
| TN | Tennessee | TN-Election_Research.md | sos.tn.gov/elections/results |
| UT | Utah | UT-Election_Research.md | electionresults.utah.gov |
| VT | Vermont | VT-Election_Research.md | electionarchive.vermont.gov |
| VA | Virginia | VA-Election_Research.md | elections.virginia.gov (JSON/CSV) |
| WA | Washington | WA-Election_Research.md | sos.wa.gov/elections |
| WV | West Virginia | WV-Election_Research.md | apps.sos.wv.gov/elections |
| WI | Wisconsin | WI-Election_Research.md | elections.wi.gov |
| WY | Wyoming | WY-Election_Research.md | sos.wyo.gov/elections |

---

## Key Findings

1. **Only California has a full official REST API** for election results
2. **Michigan** has a community-built REST API (michiganelections.io)
3. **Connecticut and Pennsylvania** offer Socrata/SODA APIs via open data portals
4. **Virginia** provides JSON data files directly — closest to API-like access without a formal API
5. **North Carolina** has the most comprehensive FTP-based data access
6. **Ohio's DATA Act (2023)** is landmark transparency legislation with daily voter snapshots
7. **New York's Flateau Act (2026)** will mandate comprehensive election data publication
8. Most states (35+) rely on basic Excel/PDF downloads with no programmatic access
9. **Wisconsin** is the most decentralized — no statewide election night reporting system
10. **North Dakota** is the only state without voter registration
