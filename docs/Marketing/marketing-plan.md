# CivicMirror — 12-Month Marketing Plan
*Prepared June 2026 · Bootstrap / Pre-seed stage · Walter LeFort, founder*

---

## 1. Executive Summary

**Three big bets for the next 12 months:**

1. **Own the "open civic data" content niche** — produce the definitive comparisons of mock vs. official election results as elections happen. No one else is publishing this dataset. It becomes the editorial anchor for every other channel.
2. **Build a civic tech / researcher beachhead** — political scientists, journalists, and civic educators are the early adopters most likely to share, cite, and link to CivicMirror. They unlock the third-party authority that makes organic and AI search self-sustaining.
3. **Launch the Coverage page as a live, updating signal** — the state-by-state adapter status page transforms a technical capability into a credibility signal and a repeatable content event each time a new state goes full-coverage.

**90-day priorities (Weeks 1–12):**
- Claim production domain, stand up public-facing infrastructure
- Publish the first mock-vs-official results post around the next available election
- Add "last synced" timestamps to the Coverage page (backend endpoint + frontend display)
- Ship `llms.txt`, `robots.txt`, and `/pricing.md` (free tier framing) before domain goes live

**12-month outcome target:**
- 5,000–15,000 monthly unique visitors (organic + direct, no paid)
- Cited in at least 3 civic tech / journalism publications
- Coverage page established as a recurring link target ("which states does CivicMirror track?")
- Email list of 500+ civic tech researchers and educators

---

## 2. Strategic Frame

### Category claim
CivicMirror is **the unrestricted public opinion mirror for U.S. elections** — the only place that compares how the open internet would vote against how eligible voters actually did.

This is a research tool, not a political tool. The category positioning is civic data infrastructure, not a social network or opinion poll.

### ICP (Ideal Audiences — ranked)
| Priority | Segment | Why they care |
|---|---|---|
| 1 | Civic tech researchers / political scientists | Unique dataset, no other source publishes this |
| 2 | Journalists covering elections / data journalism | Embeddable "internet opinion" angle for election stories |
| 3 | Civic educators (high school / college) | Real elections, no eligibility barrier — good for classroom exercises |
| 4 | Politically engaged general public | Want to "vote" on races even if ineligible or disengaged |
| 5 | Open-source / data community | Transparency of sources, open data ethos |

### Business-model logic
CivicMirror is currently **free and open**. There is no paid tier yet. The 12-month plan is pre-revenue. Marketing investment is entirely organic (time, hosting costs). The path to monetization options — data API licensing, a researcher dashboard tier, institutional subscriptions — requires first building an audience and a dataset worth paying for. This plan builds that foundation.

### Brand voice non-negotiables
- **Factual, not partisan** — never frame results as "good" or "bad" for any party or candidate
- **Transparent about limitations** — the disclaimer is always visible; mock votes are never dressed up as real ones
- **Credibly technical** — the data pipeline, source attributions, and adapter coverage are features, not footnotes
- **Accessible** — the platform requires no eligibility, no credentials, no prior knowledge

---

## 3. Current State

### Team
- 1 founder (Walter LeFort) — product, engineering, and all marketing
- AI-assisted development (Claude, GitHub Copilot)
- No marketing hire, no contractors yet

### Budget
- Pre-seed / bootstrapped
- ~$0/mo current marketing spend
- Domain purchase pending (one-time cost)
- GCP hosting for backend (existing)

### What's done
- Full-stack platform is functional: race browser, mock ballot, results comparison, coverage page
- 7 states with full SOS integration (WV, CO, SC, MA, VA, AZ, NC)
- 23 states with results adapter
- Background sync pipeline live (Google Civic, FEC, Open States, congress-legislators, OpenElections)
- Coverage page live at `/coverage` with tier breakdown
- Header nav link to Coverage already exists

### What's in flight
- Production domain (not yet purchased)
- SEO scaffolding (not yet deployed)
- Coverage page "last synced" status (optional feature, to be designed)

### What's stuck / gaps
- No domain = no indexing, no AI citations, no backlinks
- No content published yet
- No email list
- No `llms.txt`, `robots.txt`, or schema markup

### Current-state scores (0–5, scored from materials)
| Area | Score | Notes |
|---|---|---|
| Brand positioning | 4 | Clear category, voice is consistent |
| ICP clarity | 3 | Multiple ICPs; researcher beachhead needs prioritization |
| Website / landing page | 3 | Functional; hero copy strong but CTA hierarchy needs work |
| Content | 0 | Nothing published yet |
| SEO / technical | 0 | No domain yet |
| Email list | 0 | None started |
| Social presence | 0 | None started |
| PR / third-party mentions | 0 | None yet |
| Analytics | 0 | Not configured |

---

## 4. Acquisition — How Strangers Find CivicMirror

### Priority channels (90-day)

**A. Organic search (SEO content)**
The highest-leverage zero-budget channel. Full plan in the companion SEO document (`seo-plan.md`). Summary:
- Target informational queries: "mock voting platform," "how would the internet vote on [election]," "[state] election results 2026"
- Publish post-election comparison posts within 48–72 hours of certified results
- Build a `/results` archive page as a programmatic SEO target over time

**B. Researcher and journalist outreach**
- Identify 20–30 political science professors, civic tech journalists, and data journalists
- Email a cold pitch: "We're publishing unrestricted internet opinion data alongside official results. Would you be interested in early access or a citation?"
- Target publications: The Markup, FiveThirtyEight (or its successor outlets), Politico Pro data team, local data journalism shops
- Cost: $0, time only

**C. Civic tech community**
- Share on Civic Hall Slack, Democracy Works community, Personal Democracy Forum community
- Submit to civic tech directories: mySociety, Code for America, Knight Foundation grantee lists (not for funding — for visibility)
- Post on Hacker News "Show HN" on a strong election result day

### Channels to skip in Year 1
| Channel | Reason |
|---|---|
| Paid social | No budget; audience is researchers, not scroll-feed users |
| Influencer / creator | Wrong fit; this is a data tool, not a consumer product |
| Podcast sponsorships | Too expensive, too broad |
| PR firm | Not yet — do DIY outreach first; hire when there's a news hook worth pitching |

---

## 5. Activation — First Visit to Engaged User

### Current experience audit
The homepage hero is solid ("See how your community would vote.") but the activation path buries the best features:
- New visitors don't know what to do first
- The ZIP/address entry is below the fold on mobile
- There's no social proof (no "X mock votes cast" counter, no teaser result)
- The Coverage page is a nav link but not surfaced in the hero as a credibility signal

### Recommended landing page refinements (§5a)

**Hero section:**
- Current: "See how your community would vote." ✅ — keep this
- Add a trust/scale line below the subhead: something like "Tracking elections across 30 states, [N] mock votes cast so far" — real numbers build credibility
- Reorder CTAs: make "Browse races" the primary action (no signup required), demote "Register" to secondary

**Social proof strip (new section below hero):**
Add a compact strip between the hero and LocationBar with 3 numbers:
```
[50] states tracked    [N] races live    [N] mock votes cast
```
These are derivable from existing API data. Even modest real numbers beat nothing.

**Coverage link in hero:**
Add "See which states have full data →" as a tertiary link near the subhead — routes to `/coverage`. This surfaces the coverage page as a credibility signal rather than hiding it in the nav.

**First-time visitor empty state:**
When no location is set, instead of the generic "National active races" heading, show a featured race from the most recent high-profile election. Gives visitors something to interact with immediately.

### Activation success = first mock vote cast
Registration is intentionally frictionless (username + password only). The goal is to get the visitor to cast their first vote within the first session. The current flow requires:
1. See a race
2. Click through to race detail
3. Register
4. Return to race
5. Vote

Step 4 is where users drop. Consider: after registration, redirect back to the race detail page the user came from (pass `next` param through the registration flow).

---

## 6. Retention — Keeping Users Coming Back

CivicMirror's natural return trigger is **election events** — results night, certification announcements, new races being added. The platform should telegraph these moments to users who've engaged before.

### Short-term (90 days)
- Add "last synced" timestamps to the Coverage page (see §coverage-feature below) — gives returning visitors a reason to check back
- When a race result is certified in a state a user voted in, that's a natural email trigger: "The result is in for [Race] — see how your mock vote compared"

### Medium-term (6 months)
- Build a simple email digest: "New elections added in your state" — sent when the sync pipeline brings in new races
- No drip sequence needed yet; this isn't a SaaS product with a defined trial period

### Retention lever: the results comparison
The most compelling content on the platform is the mock-vs-official result side-by-side. Users who've voted in a race will want to see the final comparison. This is the stickiest screen in the product — make sure it's easy to find and share.

---

## 7. Referral — Word of Mouth

The referral mechanic for CivicMirror is **sharing results**, not a traditional referral program.

### Natural share moments
- "I voted in this mock election, here's how it compared to the real result" — shareable link to a race result page
- "My state is one of [N] with full SOS integration" — Coverage page share
- Comparison posts: "The internet voted [X%] for [Candidate] — the real result was [Y%]" — tweet-native content

### Tactics
- Add Open Graph meta tags to all race detail and result pages (enables rich previews on social)
- Add a simple "Share this result" button on race detail pages (copy link, Twitter/X, Bluesky)
- When a comparison is published (mock vs. official), make the data embeddable — a simple iframe widget or data table that journalists can drop into articles

### No referral program needed in Year 1
A formal referral program (discount codes, credits) doesn't fit this product. Focus on making the content itself shareable.

---

## 8. Revenue — Year 1 Is Pre-Revenue

CivicMirror is not monetizing in Year 1. This is intentional: the dataset needs to be established and trusted before any monetization path is credible.

### Monetization options to evaluate in Year 2
| Option | Notes |
|---|---|
| Data API access (researcher tier) | Charge academic and media institutions for API access to mock vote data; keep public browse free |
| Institutional dashboard | School / university license for classroom use |
| Grants | Knight Foundation, MacArthur, Democracy Fund — civic tech grants are a viable Y2 revenue path |
| Sponsored research reports | Commission-funded election analysis for media partners |

### Pricing readiness (do now)
Even without charging, add a `/pricing.md` file to the site root that clearly states:
- Free public browse and voting
- Future API tier (coming soon)
- Contact for institutional/researcher access

This makes CivicMirror legible to AI agents evaluating civic data tools, and signals professional intent to early institutional contacts.

---

## 9. 90-Day Roadmap

### Weeks 1–2 — Unblock
| Action | AARRR | Owner |
|---|---|---|
| Purchase production domain | Acquisition | Walter |
| Wire domain to GCP deployment | Acquisition | Walter |
| Add `robots.txt` (allow all AI bots by name) | Acquisition | Walter |
| Add `llms.txt` with product summary and key links | Acquisition | Walter |
| Add `/pricing.md` stub (free tier + coming soon) | Activation | Walter |
| Configure Google Analytics / Plausible | All | Walter |
| Add Open Graph tags to homepage, race detail, coverage pages | Referral | Walter |

### Weeks 3–4 — Foundation
| Action | AARRR | Owner |
|---|---|---|
| Publish first blog/content post (mock vs. official result comparison for next available election) | Acquisition | Walter |
| Implement Coverage page "last synced" timestamps (see ADR) | Retention | Walter |
| Add social proof strip to homepage hero | Activation | Walter |
| Fix registration `next` redirect (return user to race they came from) | Activation | Walter |
| Submit to Google Search Console | Acquisition | Walter |
| Cold email 10 civic tech researchers / journalists | Acquisition | Walter |

### Weeks 5–8 — Velocity
| Action | AARRR | Owner |
|---|---|---|
| Publish 2nd and 3rd content pieces (state coverage explainer; data sources explainer) | Acquisition | Walter |
| Post "Show HN" on Hacker News (time to an election news moment) | Acquisition | Walter |
| Add "Share this result" button to race detail pages | Referral | Walter |
| Start email list (Buttondown or Mailchimp — free tier) | Retention | Walter |
| Add Article schema to blog posts | Acquisition (SEO) | Walter |

### Weeks 9–12 — Compound
| Action | AARRR | Owner |
|---|---|---|
| Add FAQPage schema to homepage | Acquisition (SEO) | Walter |
| Publish results post for any election certified in Q3 | Acquisition | Walter |
| Send first email to list: "New states added + recent results" | Retention | Walter |
| Review analytics: which content drives registrations? | All | Walter |
| Evaluate: is any state ready to move from results → full tier? | Acquisition | Walter |

---

## 10. 12-Month Outlook

| Quarter | Milestone |
|---|---|
| Q3 2026 | Domain live, SEO foundation in place, first content published, Coverage page updated with live sync data |
| Q4 2026 | 1,000+ monthly visitors, cited in at least 1 external publication, 100+ email subscribers |
| Q1 2027 | 3,000–5,000 monthly visitors, comparison post from November 2026 elections driving backlinks, 300+ subscribers |
| Q2 2027 | 5,000–15,000 monthly visitors, evaluate Year 2 monetization options, consider applying for civic tech grant |

---

## 11. Marketing Operations Stack

| Stage | What | Skill / Tool |
|---|---|---|
| Acquisition | SEO content | `ai-seo`, `programmatic-seo` → companion `seo-plan.md` |
| Acquisition | Schema markup | `schema` skill when building blog/FAQ pages |
| Acquisition | Email outreach | Manual; no automation needed yet |
| Activation | Landing page copy | `copywriting` skill for hero iteration |
| Activation | Analytics | Plausible (privacy-respecting, simple) or GA4 |
| Retention | Email list | Buttondown or Mailchimp free tier |
| Retention | Coverage sync status | Backend `SyncLog` model → new API endpoint → frontend display |
| Referral | OG tags | `og:image` generation for race result pages |
| All | AI visibility | `llms.txt`, `/pricing.md`, `robots.txt` with AI bot allowlist |

---

## 12. Tactical Idea Bank

Selected tactics from the marketing-ideas library, rated for CivicMirror's stage:

| Tactic | AARRR | Status | Notes |
|---|---|---|---|
| Publish election comparison posts | Acquisition | **Now** | Highest-leverage unique content |
| Cold email researcher outreach | Acquisition | **Now** | 20–30 targeted, not blasted |
| Hacker News Show HN | Acquisition | **Q3** | Time to election news cycle |
| Wikipedia — add to civic tech list | Acquisition | **Q3** | High AI citation value |
| Reddit r/PoliticalDiscussion, r/DataIsBeautiful | Acquisition | **Q3** | Authentic participation only |
| Civic tech conference presence | Acquisition | **Q4** | Personal Democracy Forum, SXSW Civic |
| Guest post in data journalism outlets | Acquisition | **Q4** | The Markup, Civic Hall newsletter |
| Email digest "new elections in your state" | Retention | **Q4** | After email list has 200+ |
| Shareable race result widget (embed) | Referral | **Q4** | For journalist pickup |
| Data API (researcher tier) | Revenue | **Y2** | After dataset is established |
| Paid social | Acquisition | **Skip Y1** | Wrong channel for this ICP |
| Influencer partnerships | Acquisition | **Skip Y1** | Wrong fit |
| PR firm | Acquisition | **Skip Y1** | Do DIY first |

---

## 13. Measurement, Open Decisions, Appendix

### North-star metric
**Monthly active voters** — users who cast at least one mock vote per month. This is the metric that proves the platform has a real audience, not just visitors.

### Leading indicators (by stage)
| Stage | Metric |
|---|---|
| Acquisition | Monthly unique visitors, organic search clicks |
| Activation | % of visitors who view a race detail; % who register |
| Retention | 30-day return rate; email list size |
| Referral | External backlinks; social shares of result pages |
| Revenue | Email to researcher inquiry conversions (Y2) |

### Open decisions
| Decision | Why it matters | Target date |
|---|---|---|
| Which domain? | Everything waits on this | Week 1 |
| Blog on the main domain or subdomain? | Subdomain (blog.civicmirror.com) hurts SEO vs. main domain subfolder (/blog/) | Week 1 |
| Email tool choice? | Affects automation capability | Week 4 |
| Add comments / community features? | Could boost return visits but adds moderation burden | Q4 review |
| Apply for civic tech grants? | Relevant if Y2 revenue path is grants | Q1 2027 |

### RACI
| Task area | Responsible | Consulted |
|---|---|---|
| SEO / content | Walter | AI tools |
| Backend API (sync status endpoint) | Walter | — |
| Frontend (Coverage page update, OG tags) | Walter | AI tools |
| Email outreach | Walter | — |
| Domain / infra | Walter | — |

---

*See also: `seo-plan.md` (companion SEO document) · `adr-coverage-live-status.md` (architecture decision record for the Coverage status feature)*
