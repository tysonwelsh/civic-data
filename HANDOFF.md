# HANDOFF — resume point (2026-08-01: COUNTY DATA ACQUISITION package, owner-authorized)

> **Read in order: root `CLAUDE.md` → this file → `TODO.md` (the package checklist) →
> `GOTCHAS.md` (standing rules). Options menu: `LEADS.md`. Publish criteria: `SHIP_GATE.md`.
> One session banner, overwritten per handoff (prior banner: TODO_ARCHIVE.md anchor
> 2026-08-01-HANDOFF).**

## Where the repo stands (verified 2026-08-01T01:08 build)

The [DEBT] queue is **EMPTY**; SHIP_GATE reads P1/P2/P3 ALL PASS; the repo is on a private
git remote (`github.com/tysonwelsh/civic-data`, main) with every 2026-07-31/08-01 work
package committed. gov.db: 44/44 federation gate · caveat 92 · motion 78,561 · vote 247,459
· election_race 688 · election_result 5,482 · `check_doc_numbers.py` 13/13 · marquee
examples 5/5. G9 (public flip) is deliberately parked. **The build auto-runs the federation
gate; run `python3 scripts/check_doc_numbers.py` after any federation and reconcile what it
names.**

## THE WORK PACKAGE (owner-authorized 2026-08-01, from live owner queries)

The owner tested the repo with "who was the single largest donor for county-level races in
Salt Lake County?" — unanswerable twice over. Authorized response, two packages:

### Package A — SLCo county-office ELECTION RESULTS

**Gap:** `election_result` holds county-office contests (Commission/Sheriff/Clerk/Assessor/
Attorney, even-year `general`/`primary` types) for summit (2006–2024), weber (2006–2024),
utah (2016–2024), juab (2024) — but **salt_lake_county's 2,172 rows are odd-year MUNICIPAL
canvasses only**. The county's own offices (Mayor, 9 Council seats, Sheriff, row offices)
have zero result rows. Also: NO county-office race anywhere has an audited `election_race`
row (that layer is city-only).

**Deliverables:** (1) acquire SLCo even-year canvasses (Clerk's archive; same SOVC family
formats the archive normalizer already parses — recon the depth, aim to match the 2007+
municipal depth, floor negotiable at recon); (2) land raws + normalized rows IN-REPO at
`salt_lake_county/elections/` per the county canvass conventions (washington/juab pattern —
NOT the ~/Desktop archive, which is local-only and unpublishable); (3) federate as
`election_type='general'/'primary'` rows; (4) promote SLCo county-office winners into the
AUDITED `election_race` layer (25-col conventions, cross-checked winners); (5) file the
other-counties election_race promotion as a follow-on lead. ⚠ Washington claims canonical
elections "2018–2025" but federates municipal-2019+ only — verify at its source while in
this area (LEADS.md, observation not diagnosis).

### Package B — county-candidate CAMPAIGN FINANCE, 7 counties

**Gap:** `cf_contribution` has zero county-entity rows anywhere. **Scope: the 7 counties
with a repo city** — salt_lake, utah, weber, cache, summit, washington, juab. (OWNER
QUESTION to raise at plan time: wasatch — park_city's second straddle county — is
registered-only with no build; include its CF?)

**Deliverables per county:** a `campaign_finance/` dataset in the county entity dir per the
city conventions (index.csv + raw/ + text/ + AVAILABILITY.md + CLAUDE.md; structured
contributions/expenditures/cycle_totals via the shared `scripts/campaign_finance/` lib
where filings support it; `cf-vision-transcribe` for scans — the $0-API default). Recon
each county's channel first: county clerk disclosure pages AND the state
`disclosures.utah.gov` system (which carries county-office candidates — a real channel
here, unlike the municipal layer where it was gap-filler only). ⚠ The cf federation loader
may be CITY-scoped — check `build_search_layer.py`'s cf loaders and extend for county
entities if needed (shared-script change: backup + prove city rows byte-identical).
Db-less washington/juab still get the dataset (their modules federate without a db).

## Discipline (unchanged, load-bearing)

Recon BEFORE acquisition (write/extend each county's recon notes); cardinal rules (honest
gaps are data; verbatim values never overwritten; derived layers regenerated); backups to
`_backups/<date>-county-acquisition/`; conflict-planned agent waves with ONE federation at
the end; **agent launches (count/model/effort) are presented for OWNER APPROVAL first —
Opus default, Fable where judgment-heavy** (memory: approve-agent-launches); leads →
LEADS.md; new debt needs primary-source evidence; a closure that falsifies a doc claim
fixes the doc in the same session; after federation run check_doc_numbers + reconcile
(election_race 688 and election_result 5,482 WILL move). PRIVACY.md applies: county CF
text layers ship verbatim (donor addresses included, documented); structured rows carry
donor city/state only. Add caveat rows for whatever ceilings the sources impose, and
update the cf-coverage caveat (it currently says "29 of 31 cities" — county coverage
changes its text).

## Operational pointers

- SLCo SOVC parsing: the proven normalizer families live at
  `~/Desktop/slco-election-archive/scripts/normalize_sovc.py` (local-only) — port what's
  needed INTO the repo rather than deepening the desktop dependency.
- County canvass conventions: `washington_county/elections/` + `juab_county/elections/`
  are the reference implementations; `salt_lake_county/elections/` holds the municipal
  canonical already (extend, don't disturb).
- CF conventions: any built city's `campaign_finance/CLAUDE.md` + the shared lib +
  `.claude/skills/cf-vision-transcribe/`. Never sum cf_filing columns; cycle_totals rules.
- The federation build is hardened (lockfile + atomic + auto-gate); never run it while
  agents are live; ONE federation per package.
