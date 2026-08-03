# Changelog

## [0.2.0](https://github.com/CivicMirror/CivicMirror/compare/v0.1.0...v0.2.0) (2026-08-03)


### Features

* add /coverage page showing state adapter coverage tiers ([af8e158](https://github.com/CivicMirror/CivicMirror/commit/af8e1581f3ba38f004d89cdb8aa52b8a434384b1))
* add time-based filter (Month/Year/Historical) to race browser ([c196a97](https://github.com/CivicMirror/CivicMirror/commit/c196a97709b88ce67f9231b1d026f3b2edc011e7))
* contest type pill + filter (ballot_type population, ContestTypeFilter, URL sync) ([59ac7c9](https://github.com/CivicMirror/CivicMirror/commit/59ac7c9dde7498ba0d207b34c5a92461fd237327))
* **coverage:** add NC to full coverage tier ([6a29287](https://github.com/CivicMirror/CivicMirror/commit/6a292878a31bdce8b9e0ba71b7042d86d3cedbb7))
* **coverage:** auto-promote states to results tier via adapter registry ([1a11d15](https://github.com/CivicMirror/CivicMirror/commit/1a11d1524a199a436337c26412e85803f5bc5429))
* **coverage:** implement live sync status on Coverage page (ADR-001) ([e6d937c](https://github.com/CivicMirror/CivicMirror/commit/e6d937c5eedfd5905b22bd2acda57f5736cea8ef))
* **frontend:** add FAQ and Contact Us pages, link from footer ([d9146fd](https://github.com/CivicMirror/CivicMirror/commit/d9146fd8e352e870d140684f39e037da37ade06e))
* **frontend:** add office/jurisdiction search to homepage race list ([87026e1](https://github.com/CivicMirror/CivicMirror/commit/87026e13c60fb903f23e9ec250f7b60d60fce607))
* migrate election data reads to CivicMirror-API (Phases 1, 2, 5) ([2c60887](https://github.com/CivicMirror/CivicMirror/commit/2c60887027211dbc01d01ea023eeda8860c1bf38))
* migrate race detail and official results to CivicMirror-API (Phases 3, 4) ([2be17a0](https://github.com/CivicMirror/CivicMirror/commit/2be17a01b444231cc6463a06c2c6f9fab714d898))
* **PartyPill:** add colors for WFP (Working Families) and CON (NY Conservative) ([#24](https://github.com/CivicMirror/CivicMirror/issues/24)) ([979dd0d](https://github.com/CivicMirror/CivicMirror/commit/979dd0df58e1bf0c0203770c66ff6552936899e0))
* **seo:** add robots.txt, llms.txt, OG tags, JSON-LD schema, sitemap.xml ([e082abd](https://github.com/CivicMirror/CivicMirror/commit/e082abd5cb26848d2b19a43cfb020729c0d31362))
* **ui:** append ★ to incumbent candidate labels ([ac7a5f5](https://github.com/CivicMirror/CivicMirror/commit/ac7a5f55e35ddc0341702ae5af7301d4f849074c))
* **ui:** landing page and coverage page marketing refinements ([e00cb72](https://github.com/CivicMirror/CivicMirror/commit/e00cb72cb9dd449db9ec2a4f64afbc04d608d0f6))
* **ui:** replace large race cards with compact two-line summary rows ([60e9ef2](https://github.com/CivicMirror/CivicMirror/commit/60e9ef20b2066c7570c489f9c14ef2ec1b1f797a))


### Bug Fixes

* add X-Api-Key header to apiClient for voting endpoints ([f028026](https://github.com/CivicMirror/CivicMirror/commit/f02802633056a88aba91fde6edace83d970074de))
* address PII and IP geolocation consent issues ([7903189](https://github.com/CivicMirror/CivicMirror/commit/7903189fec65141e264b907cfefaac996cb56230))
* always surface fetch errors and use dynamic resultStatus description ([a44198d](https://github.com/CivicMirror/CivicMirror/commit/a44198d7749699d6cea02a378b4ac9469dbfc0f3))
* break URL↔store bidirectional sync loop in useRaceFilters ([517376b](https://github.com/CivicMirror/CivicMirror/commit/517376b41da280102ef993f7152e40b71bbbede0))
* clear stale location fields on scope switch; guard electionId=0 ([300b8f7](https://github.com/CivicMirror/CivicMirror/commit/300b8f7a78aa70d7a258b9c6e60028212b734d3e))
* ContestTypePill handles ballot-measure (Civic API actual return value) ([af9140d](https://github.com/CivicMirror/CivicMirror/commit/af9140d63407f6dde6e06975f03f0124555c9f2a))
* **coverage:** clarify tier data descriptions ([816bc3b](https://github.com/CivicMirror/CivicMirror/commit/816bc3b19510c41b13d8b8ccfdf9980652fb4092))
* **coverage:** consume live coverage tiers ([0846d41](https://github.com/CivicMirror/CivicMirror/commit/0846d418b01e7dbdca39945d025c50f65dbd37e1))
* **format:** add timeZone: UTC to date-only formatter ([b1ec56d](https://github.com/CivicMirror/CivicMirror/commit/b1ec56d1bb848fe08a3dcc2212f30d8a99cc8c4d))
* **frontend:** cast mock votes against the PK route, not the stale ext/canonical_key route ([25a03a8](https://github.com/CivicMirror/CivicMirror/commit/25a03a8149af7cd2e94568ebe986ea62a0287160)), closes [#16](https://github.com/CivicMirror/CivicMirror/issues/16)
* **frontend:** point community race submission at the real endpoint ([8560963](https://github.com/CivicMirror/CivicMirror/commit/8560963edebb9c33c1a664b3f6a688f707df391d))
* **frontend:** point My Votes at the deployed CivicMirror-API endpoint ([#17](https://github.com/CivicMirror/CivicMirror/issues/17)) ([46a798a](https://github.com/CivicMirror/CivicMirror/commit/46a798a5b9694a85535ad5a4656a8453563e8435))
* **frontend:** proxy /django-admin and /static to the API container ([3118f3e](https://github.com/CivicMirror/CivicMirror/commit/3118f3e592f99b9c930fd01273be686265e63920))
* **frontend:** proxy api requests through nginx ([c21b123](https://github.com/CivicMirror/CivicMirror/commit/c21b123a1a9d34a4950cf7176462b00f62e39a24))
* **frontend:** restore session on refresh and fix candidate vote payload ([c58e496](https://github.com/CivicMirror/CivicMirror/commit/c58e49683a2b89e8348682893ba7116127854141))
* **frontend:** show party in mock tally; recognize already-cast votes on load ([1a22840](https://github.com/CivicMirror/CivicMirror/commit/1a22840e0437916f034fe183953534181236e932))
* migrate state/national scope from embedded backend to CivicMirror-API ([20ce052](https://github.com/CivicMirror/CivicMirror/commit/20ce052d4bed74834beeb2dbc65264f5b5022be8))
* **national-scope:** filter elections and races to jurisdiction_level=national ([2ded06f](https://github.com/CivicMirror/CivicMirror/commit/2ded06f58ec1eab6ee284c7305e8d5c8957652cb))
* pass date bounds to listRaces and increase elections page_size ([3c5a450](https://github.com/CivicMirror/CivicMirror/commit/3c5a45023fd4596d06ba2a92b0cf43c64da76d62))
* registration fails in production due to missing TermsOfUseVersion ([14ab3fe](https://github.com/CivicMirror/CivicMirror/commit/14ab3feabc32e640c57b989d25103937cfbce2f6))
* replace country free-text input with ISO alpha-2 dropdown ([19086e5](https://github.com/CivicMirror/CivicMirror/commit/19086e53d34551c532fa8d448676d4cd1021a2e4))
* show specific field errors on registration instead of generic 400 ([29d7a1f](https://github.com/CivicMirror/CivicMirror/commit/29d7a1f1940b0096cbbc12b971b1b33123aa6fd8))
