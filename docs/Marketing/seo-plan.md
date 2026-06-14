# CivicMirror — SEO & AI Search Plan
*Prepared June 2026 · Backend-ready; deploy when domain is purchased*

---

## Overview

CivicMirror has a zero-budget acquisition window before any paid channels are viable. SEO and AI search visibility are the primary levers. This plan is structured in two phases:

- **Phase 1 — Technical foundation** (deploy on domain purchase day; no content required)
- **Phase 2 — Content and authority** (ongoing, starting Week 3)

The backend wiring described here should be complete before the domain goes live so Day 1 indexing starts clean.

---

## Phase 1 — Technical Foundation (Wire Now, Deploy on Domain Day)

### 1.1 `robots.txt`

Allow all AI crawlers by name. Blocking these crawlers prevents citation even if content ranks.

```
User-agent: *
Allow: /

# AI search bots — allow citation
User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Bingbot
Allow: /

# Block training-only crawlers (not search bots)
User-agent: CCBot
Disallow: /

Sitemap: https://[your-domain.com]/sitemap.xml
```

Place this file at the domain root. Wire it to the Nginx config / GCP Cloud Run static serving before domain goes live.

---

### 1.2 `llms.txt`

Gives AI systems a quick overview of CivicMirror when they encounter the domain. Place at `/llms.txt`.

```markdown
# CivicMirror

CivicMirror is an open civic engagement platform that imports real U.S. election data and allows anyone to cast a mock vote, regardless of age, citizenship, or country of residence. After official results are certified, the platform compares mock vote outcomes against real-world results.

## What CivicMirror Is

- Public mock voting platform for real U.S. elections
- No eligibility restrictions — anyone worldwide can participate
- Data sourced from Google Civic API, OpenFEC, Open States, OpenElections, and others
- Covers all 50 states; 7 states with full SOS integration, 23 with results adapters

## Key Pages

- Homepage / Race Browser: /
- State Coverage: /coverage
- Pricing (free): /pricing.md
- Registration (free): /register

## What CivicMirror Is Not

- Not an official election authority
- Not affiliated with any government agency or political organization
- Mock votes have no legal effect

## Contact

For researcher or institutional access inquiries: [contact email when set up]
```

---

### 1.3 `/pricing.md`

Machine-readable pricing for AI agents that evaluate civic data tools. Place at `/pricing.md`.

```markdown
# Pricing — CivicMirror

## Public (Free)
- Price: $0/month
- No account required
- Features: Browse all races, view live mock tallies, view official certified results, compare mock vs. official results

## Registered User (Free)
- Price: $0/month
- Account required (username + password, no email verification)
- Features: Everything in Public, plus cast mock votes (one per race), view personal vote history, submit local races

## Researcher / Institutional Access (Coming in 2027)
- Price: Contact for details
- Features: Data API access to mock vote dataset, bulk export, custom query support
- Contact: [email when set up]
```

---

### 1.4 `sitemap.xml`

The sitemap should be generated dynamically by the backend. At minimum it must include:

- `/` — homepage
- `/coverage` — coverage page
- `/races/{id}` — each public race detail page
- Future: `/blog/{slug}` when content is published

Wire the Django backend to expose `/sitemap.xml` via the `django.contrib.sitemaps` framework. This is a single-day backend task.

**Django sitemap wiring sketch:**

```python
# config/urls.py addition
from django.contrib.sitemaps.views import sitemap
from elections.sitemaps import RaceSitemap, StaticViewSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'races': RaceSitemap,
}

urlpatterns += [
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]
```

```python
# elections/sitemaps.py (new file)
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Race

class RaceSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        return Race.objects.filter(status__in=['active', 'results_certified'])

    def location(self, obj):
        return f'/races/{obj.id}'

    def lastmod(self, obj):
        return obj.updated_at


class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'weekly'

    def items(self):
        return ['home', 'coverage']

    def location(self, item):
        return reverse(item)
```

---

### 1.5 Open Graph meta tags

Add to the React app's `index.html` (static defaults) and override dynamically on key pages.

**Static defaults in `index.html`:**

```html
<meta property="og:type" content="website" />
<meta property="og:title" content="CivicMirror — Public mock voting for real elections" />
<meta property="og:description" content="Browse real U.S. election contests, cast a mock vote, and see how open internet opinion compares to the official result." />
<meta property="og:image" content="https://[domain]/og-default.png" />
<meta property="og:url" content="https://[domain]/" />
<meta name="twitter:card" content="summary_large_image" />
```

**Dynamic OG tags on race detail pages:**
Use `react-helmet-async` or Vite's SSR meta injection to set race-specific titles and descriptions. Until SSR is available, the static defaults above serve all pages — acceptable for launch.

The `og-default.png` image should be a simple 1200×630 branded card. Can be designed with Figma or Canva.

---

### 1.6 Submit to Google Search Console

Day 1 after domain goes live:
1. Add property in Google Search Console
2. Verify via DNS TXT record or HTML file
3. Submit sitemap URL
4. Request indexing for `/`, `/coverage`, and first content page

---

## Phase 2 — Content & Authority (Week 3 Onward)

### 2.1 Target Query Categories

| Query category | Example queries | Content type |
|---|---|---|
| Platform category | "mock voting platform," "open civic participation tool," "internet opinion polling" | Homepage, About page |
| Comparison queries | "how would the internet vote on [election]," "mock vote vs real vote comparison" | Post-election comparison posts |
| State coverage | "[state] election results 2026," "CivicMirror [state] coverage" | Coverage page + state-specific content |
| Research / data | "unrestricted voting data," "open election participation data," "civic tech election API" | Researcher-facing landing page |
| How-to / explainer | "how does mock voting work," "what is CivicMirror," "how to track election results" | FAQ page, About page |

**Fan-out queries to cover on the Coverage page:**
- "which states does CivicMirror track"
- "[state abbreviation] election data"
- "state election results tracker"
- "civic data coverage by state"

---

### 2.2 Content Cadence

| Content type | Frequency | Trigger | Primary query target |
|---|---|---|---|
| Mock vs. official results comparison post | Per election cycle | Within 48–72h of certified results | "[election name] internet vote comparison" |
| State coverage explainer | Once (evergreen) | Week 3 | "CivicMirror state coverage" |
| Data sources explainer | Once (evergreen) | Week 4 | "CivicMirror data sources," "civic election data APIs" |
| Platform FAQ | Once (evergreen) | Week 5 | "what is CivicMirror," "how does mock voting work" |
| Researcher/academic landing page | Once | Week 6 | "open civic participation data," "election mock vote API" |

---

### 2.3 Comparison Post Template (highest-value content type)

Every post-election comparison post should follow this structure for maximum AI extractability:

```markdown
# [Election Name]: How the Internet Voted vs. the Official Result

*Published: [date] · Data updated: [date]*

## Summary

In the [election name], [Candidate A] won with [X%] of the official vote.
CivicMirror's open mock vote — cast by [N] participants with no eligibility restrictions —
showed [Candidate A/B] leading with [Y%] before results were certified.

| | Mock Vote (CivicMirror) | Official Result |
|---|---|---|
| [Candidate A] | Y% | X% |
| [Candidate B] | Z% | W% |
| Margin | ... | ... |
| Participants / Voters | [N mock] | [N official] |

## About This Data

CivicMirror imports real election data from [source] and allows anyone worldwide to cast 
a mock vote. [N] people participated in the mock ballot for this race.

Mock votes have no legal effect and do not represent official results. 
[Full disclaimer link]

## How the Mock Vote Compared

[2–3 paragraphs of analysis — factual, no partisan framing]

## Methodology

- Data source: [Google Civic API / state SOS name]
- Mock votes collected: [date range]
- Registration: username and password only, no eligibility check
- One mock vote per user per race

## About CivicMirror

CivicMirror is an open civic engagement platform...
```

**Why this structure works for AI SEO:**
- Self-contained summary block (40–60 words) → extractable by AI engines
- Comparison table → highest-citation content type (~33% of AI citations)
- Statistics with source attribution → +37–40% citation boost (Princeton GEO research)
- Named methodology → E-E-A-T signal for research credibility
- "Last updated" date → freshness signal

---

### 2.4 Coverage Page SEO Enhancements

The existing `/coverage` page is already a strong SEO target. Enhancements to add:

**Structured data for the Coverage page:**

Add `FAQPage` schema to the Coverage page to capture FAQ-style queries:

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Which states does CivicMirror have full coverage for?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "CivicMirror has full SOS integration for West Virginia, Colorado, South Carolina, Massachusetts, Virginia, Arizona, and North Carolina. Full coverage means elections, races, candidates, and live results are ingested directly from the state source."
      }
    },
    {
      "@type": "Question", 
      "name": "What does 'Results Adapter' mean on CivicMirror?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "A Results Adapter means CivicMirror can display live election-night results for that state when configured per election. Elections and races for these states come from the national Civic data feed."
      }
    },
    {
      "@type": "Question",
      "name": "Does CivicMirror cover all 50 states?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. All 50 states have elections and races available via the national Civic data feed. 7 states have full SOS integration with live results, 23 have a results adapter, and the remaining states have elections and candidate data only."
      }
    }
  ]
}
```

Inject this via a `<script type="application/ld+json">` in the Coverage page `<head>`.

**Add an introductory text block to Coverage page:**

Before the tier breakdown, add a 2–3 sentence paragraph that is AI-extractable as a standalone answer to "which states does CivicMirror cover?":

> CivicMirror tracks election data across all 50 U.S. states. Seven states — West Virginia, Colorado, South Carolina, Massachusetts, Virginia, Arizona, and North Carolina — have full SOS integration with direct ingestion of elections, races, candidates, and live results. All remaining states have race and candidate data available via the national Civic Information feed.

---

### 2.5 Homepage SEO Additions

**FAQ section below the race list:**

Add a collapsible FAQ section at the bottom of the homepage (visible to crawlers, collapsed by default for UX):

```
Q: What is CivicMirror?
A: CivicMirror is an open civic engagement platform...

Q: Is CivicMirror an official voting platform?
A: No. Mock votes on CivicMirror have no legal effect...

Q: Who can participate?
A: Anyone worldwide can browse races and cast mock votes...

Q: How is the data sourced?
A: CivicMirror imports real election data from the Google Civic Information API...
```

Pair with `FAQPage` schema markup.

**Add `Organization` schema to homepage:**

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "CivicMirror",
  "url": "https://[domain]/",
  "description": "Open civic engagement platform for unrestricted mock voting on real U.S. elections",
  "foundingDate": "2026",
  "sameAs": []
}
```

---

### 2.6 AI Visibility Monitoring (Manual, No Tools Required)

Monthly check — run these 10 queries across ChatGPT, Perplexity, and Google:

| Query | Check |
|---|---|
| "mock voting platform" | Is CivicMirror mentioned? |
| "how would the internet vote on [recent election]" | Is CivicMirror cited? |
| "which states does CivicMirror cover" | Is the Coverage page cited? |
| "open internet voting data" | Any mention? |
| "civic election data API" | Any mention? |
| "CivicMirror" | What do AI engines say about us? |
| "unrestricted voting platform" | Any mention? |
| "[election name] mock vote" | After publishing comparison post |
| "CivicMirror [state]" | After state-specific content |
| "CivicMirror vs [competitor]" | If any comparable tools emerge |

Log results in a simple spreadsheet. Track month-over-month.

---

## Phase 2 — Backlink and Authority Building

### Priority backlink targets

| Target | Why | How |
|---|---|---|
| Wikipedia — List of civic technology | High AI citation weight (7.8% of ChatGPT citations) | Add CivicMirror when it has a production URL |
| Civic Hall newsletter / blog | Civic tech audience, backlink from authoritative domain | Pitch a guest post after first election comparison post |
| The Markup | Data journalism outlet, high domain authority | Pitch a data story angle using the mock vs. official comparison data |
| Code for America blog | Civic tech community | Submit to their "what we're reading" roundup |
| State SOS / election official websites | Niche but highly relevant domain authority | Some states link to third-party civic tools — submit after full launch |
| Muck Rack / journalism databases | Journalists find tools here | List CivicMirror as a data journalism resource |
| Personal Democracy Forum | Annual conference, online community | Share the platform in community discussion |

---

## Backend Wiring Checklist (Ready to Deploy)

These are the backend tasks that should be completed before domain goes live, so they're wired and ready:

- [ ] `sitemap.xml` endpoint (Django sitemaps framework — see §1.4)
- [ ] `robots.txt` static file at domain root (see §1.1)
- [ ] `llms.txt` static file at domain root (see §1.2)
- [ ] `/pricing.md` static file at domain root (see §1.3)
- [ ] `SyncLog` summary endpoint for Coverage page (see ADR `adr-coverage-live-status.md`)
- [ ] Open Graph meta tags on race detail pages (see §1.5)
- [ ] `FAQPage` schema injection on homepage and Coverage page (see §2.4–2.5)
- [ ] `Organization` schema on homepage (see §2.5)
- [ ] Google Search Console property created, sitemap submitted (Day 1 after domain)

---

## Summary: SEO Priority Stack

| Priority | Action | Impact | Effort |
|---|---|---|---|
| 1 | `robots.txt` with AI bot allowlist | Enables all AI citation | 30 min |
| 2 | `llms.txt` | Improves AI understanding of the product | 1 hour |
| 3 | `sitemap.xml` | Enables complete indexing | Half day |
| 4 | Search Console submission | Accelerates indexing | 1 hour |
| 5 | Open Graph tags | Enables social sharing rich previews | Half day |
| 6 | Coverage page FAQ schema | Captures high-value "which states" queries | 2 hours |
| 7 | First comparison post | Backlink magnet, unique content | Per election |
| 8 | Homepage FAQ section + schema | Captures "what is CivicMirror" queries | Half day |
| 9 | `/pricing.md` | AI agent legibility | 30 min |
| 10 | Wikipedia listing | Long-term AI citation weight | 1 hour |

---

*See also: `marketing-plan.md` (12-month strategy) · `adr-coverage-live-status.md` (architecture decision for live sync status feature)*
