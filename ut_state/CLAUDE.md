# State of Utah (ut_state) — state-tier data repository

The repo's **first state-tier entity** (fed_index **301**, `gov_level='state'`, dir
`ut_state/`; registry `registry/entities.csv`). Federates into repo-root `gov.db`
(`cities.db`) as `gov_level='state'`, above the county tier (Salt Lake County) and the 31
city/town entities. Like a county, the state is modeled as **modules**, not a big city — four
of them, each answering a different question about the legal + demographic frame the local
governments operate inside. Source map + channel verdicts: **`recon.md`**. Read this file
before analyzing ut_state.

The four modules and what each is FOR:

- **`legislation/`** — the Legislature's bill + roll-call record (land-use/housing subset). The
  state law being MADE, and how each legislator voted.
- **`advisory_opinions/`** — the Property Rights Ombudsman's numbered opinions. The state's
  read on specific local land-use disputes — the highest-value cross-link to the local record.
- **`statutes/`** — the verbatim LUDMA + Ombudsman Act code. The statutory backbone under every
  rezone/subdivision/exaction/MIH action in the repo.
- **`projections/`** — Gardner state-grain population/household/jobs. The top-of-hierarchy
  growth denominator above the county and city projection tiers.

## legislation/ — bills + named roll-call votes (land-use/housing subset)

**Scope:** Utah **General Sessions 2015GS–2026GS** (12 sessions), a **264-bill land-use/housing
subset** selected from all **9,478** enumerated bills by an **auditable classifier**
(`legislation/classify.py`): keyword rules over bill TITLES (land use / zoning / subdivision /
annexation / impact fee / housing / ADU / density / general plan / incorporation-township /
development / eminent domain / building code) + 5 self-validating named anchors (SB34-2019,
HB82-2021, HB462-2022, HB406-2023, SB168-2024). Every kept bill records the matched rule in its
`relevance` column. **Over-inclusion is intentional; silent exclusion is not.** Recall ceiling:
title-based, so a land-use bill with a generic title can be missed (the anchors backstop the
landmarks).

**Votes: 1,208 roll calls, 27,887 NAMED votes** — full named floor + committee roll calls,
scraped from the **le.utah.gov PUBLIC website** (no account). This differs from every city/county
(they come from minutes): the le.utah.gov developer API carries bill metadata but **no votes** and
needs an owner-gated developer token (not used); **LegiScan** (`getRollCall`, bulk datasets) is a
free-account-gated **alternative**, documented in `recon.md`, not registered. Two public page
types give full named roll calls — **floor** `DynaBill/svotes.jsp` (Yeas/Nays/Absent, every
member named) and **committee** `mtgvotes.jsp` (named standing-committee votes). **Voice votes**
appear as roll-call rows with no names (`names_recorded=0`, `result_raw='Voice vote'`) — an honest
recording ceiling. **Party and district are NOT on the public vote pages** — `vote` rows carry
name + chamber + value only (honest blank; mappable later from roster pages / the gated API).

**Legislators are a DISJOINT person population.** In the db, `person` rows for ut_state carry
`city='ut_state'` and are **never merged with municipal persons** — keyed on the full verbatim
name (`Last, F.`), over-split beats wrong-merge (surnames collide across the 222 legislators).

## advisory_opinions/ — Property Rights Ombudsman opinions (the cross-link layer)

The full numbered set of **Advisory Opinions of the Office of the Property Rights Ombudsman
(OPRO)**, issued under Utah Code **§ 13-43-205** — each a written prediction of how a court would
decide a specific Utah land-use dispute between a property owner/developer and a city or county.
**They interpret LUDMA — the act every city and county in this repo administers** — so an opinion
naming a repo entity is the state's read on a dispute that same council or PC handled.

- **`index.csv` = 309 rows** (opinion universe 1→309), **307 fetched** (PDF + `pdftotext -layout`
  sidecar in `text/`), issue dates 2006-07-05 → 2025-08-01. `repo_entities_matched` flags the
  **117 opinions whose Parties line names a repo entity** (**28 distinct** — most-referenced:
  Summit County 14, Park City 13, Salt Lake City 9, Lehi 8, Provo 8, Draper 7, Cottonwood Heights
  6). A convenience name-match, NOT a verified holding — confirm against the opinion text before
  quoting.
- **Honest gaps:** **#102** and **#206** have no recoverable PDF on either host (blank `path`,
  recorded as gap rows, never filled). **#142** and **#145** are **image-only scans** (`pdftotext`
  got <10 chars) — present but **unindexed by FTS**, `date`/`title` blank (not fabricated); a
  vision OCR pass could recover them.
- **Retrieval (Cloudflare):** both `propertyrights.utah.gov` and `commerce.utah.gov` sit behind
  Cloudflare and 403 every machine fetch, so the set was enumerated + pulled through the **Wayback
  Machine** (CDX API → `web.archive.org/web/<ts>id_/<url>`). `source_url` in `index.csv` is the
  **original** OPRO URL (durable citation); Wayback is only the fetch channel. OPRO's newer
  year-sequential `Advisory-Opinion-2025-NN` scheme is a documented follow-up, not ingested.

## statutes/ — verbatim LUDMA + Ombudsman Act (218 sections)

Verbatim current text of the three Utah Code chapters **every city and county in this repo
administers**, lifted from the official `le.utah.gov` chapter XML (Office of Legislative Research
and General Counsel). One plain-text file per section (`text/<chapter>/<section>.txt`), verbatim
with native subsection labels/nesting + a `[History: …]` line; `index.csv` one row per section
(`doc_class=statute`).

### The 2025 LUDMA recodification (HEADLINE FINDING — read this)

Both LUDMA chapters were **renumbered and amended effective 11/6/2025** (2025 Special Session 1).
**Repo city/county docs cite the OLD numbering** — translate when cross-referencing:

| act | OLD (repealed) | CURRENT | sections here |
|---|---|---|---|
| Municipal LUDMA | Title 10 Ch **9a** | **Title 10 Ch 20** | 109 |
| County LUDMA | Title 17 Ch **27a** | **Title 17 Ch 79** | 101 |
| Property Rights Ombudsman Act | (unchanged) Title 13 Ch 43 | Title 13 Ch 43 | 8 |

The moderate-income-housing / housing-preemption provisions (old `10-9a-403` area) are now
**`10-20-403`** (Moderate income housing element). Third-party mirrors (Justia/FindLaw) are still
stale on the old numbers; `le.utah.gov` is the only current source. Legislature crosswalks + the
byte-verified XML ledger are in `statutes/SOURCES.md`. Point-in-time snapshot (retrieved
2026-07-20); scope = these three chapters only (impact-fee Title 11 ch. 36a, sunset Title 63I,
etc. are out of scope).

## projections/ — Gardner state-grain growth forecast (140 rows)

Long-term **population, household, and employment** projections for the **State of Utah** from the
**Kem C. Gardner Policy Institute** (Utah's official series) at STATE grain — the top-of-hierarchy
denominator above `salt_lake_county/projections/` and the city tiers. Canonical:
`ut_state_projections.csv` (9-col repo projection schema, 7 metrics). Two vintages coexist by
design — **Vintage 2025 (Nov 2025)** 2025→2065 (current) + **Vintage 2022 (Jan 2022)** with
historical base 2010/2015 → 2060; **filter to one, never mix in a trend line**. `population` is
total population; `households` ≠ housing units (occupied only). **Baseline-only — no scenario
variants:** the public Gardner State-and-County workbooks have **no scenario dimension at state
grain** (one series per year); high/low sensitivity figures exist only as narrative in briefs, so
`scenario='baseline'` on every row and nothing was fabricated (the earlier scenario-variant
expectation was wrong — see `projections/SOURCES.md`).

## Which artifact for which question

- **A land-use bill's votes / who voted how:** `db/ut_state.db` `motion`+`vote` (join `application`
  on the bill), or `legislation/votes.csv` (+ `votes_recovered.csv` for 2025/2026 floor).
- **What land-use bills passed a session / effective dates / chapters:** `legislation/bills.csv`.
  Why a bill is in-scope: its `relevance` column. Widen the net: `bills_all.csv` (relevance '' =
  classified out).
- **The state's read on a specific local land-use dispute / opinions naming a repo entity:**
  `advisory_opinions/index.csv` (`repo_entities_matched`) → the `text/AO-<NNN>.txt` sidecar.
- **What the statute actually says (current numbering):** `statutes/text/<chapter>/<section>.txt`.
  Translate old 10-9a / 17-27a citations via the recodification table above.
- **Statewide growth / housing-demand denominator:** `projections/ut_state_projections.csv` (fed
  `cities.db` `projection` where `city='ut_state'`).
- **Thematic keyword search:** `cities.db` FTS layers cover the minutes/motions/ordinances corpus;
  ut_state legislation motions federate into `motion` where `city='ut_state'`.

## The database (`db/ut_state.db`) — standard 8-table schema

Built from the legislation CSVs; federates unchanged (`gov_level='state'`). Totals: **23 bodies**
(House, Senate, named standing committees; `kind` chamber | committee), **222 persons**
(legislators, DISJOINT — `city='ut_state'`), **541 meetings** (roll-call events `(body,date)`),
**264 applications** (one per BILL, `app_key='bill:<session>:<bill>'`), **1,208 motions** (one per
roll call; `motion_type` floor 869 / committee 339; `result_raw` = verbatim `Y-N-A` or
`Voice vote`; **378 voice/unrecorded** with `names_recorded=0`), **27,887 votes** (per-legislator
Yea/Nay/Absent), **729 role** rows, **referral** present-but-empty (the federator needs it).
`motion.outcome`: 820 Pass / 10 Fail / 378 blank (voice/unrecorded).

## Honest gaps / follow-ons (queue in root TODO.md)

- **2025GS + 2026GS committee votes** — residual gap: those two sessions' bill STATIC pages are
  broken JS shells (stale 2024 placeholder rows inside HTML comments — `harvest_bills.py` strips
  comments so they correctly yield ZERO fake votes). Their real **floor** votes ARE recovered by
  crawling `svotes.jsp` voteids directly (`harvest_shell_recovery.py` → `*_recovered.csv`, in the
  db); **committee** (mtgvotes) votes for these two sessions are not swept (the voteid space is
  global, not session-scoped). **Cosmetic artifact:** `legislation/bills.csv` shows `n_rollcalls=0`
  for the 2025/2026 shell-session bills even though their floor votes exist in `*_recovered.csv`
  and the db — the count column was populated from the (stripped) static pages, not the recovery
  files. Trust the db / recovered CSVs for those sessions, not the `bills.csv` count column.
- **Party + district** absent from `vote` (public vote pages omit them) — honest blank; map from
  the roster pages or the gated API later.
- **Special sessions** not yet swept (rare land-use content) — enumerate `<YEAR>S<N>`, classify,
  append.
- **advisory_opinions:** #102/#206 unrecovered gaps; #142/#145 image-only (vision OCR follow-up);
  OPRO's year-sequential 2025-NN naming not yet deduped into the global set.
- **statutes:** point-in-time only (no prior-version / annotation apparatus); three chapters only.
- **projections:** single baseline scenario (no state-grain variants published); no housing-unit
  (vacancy-inclusive) figure — households is the proxy.
- **Developer API token** (owner-gated) and **LegiScan** (free-account gated) — documented
  acquisition leads only; neither adds votes the public channel doesn't already give.

## Rebuild

```
python3 ut_state/legislation/parse_billlists.py        # (re)harvest billlist.jsp if refreshing
python3 ut_state/legislation/harvest_bills.py           # 2015-2024 bill+vote pages -> CSVs (resumable)
python3 ut_state/legislation/harvest_shell_recovery.py  # 2025GS+2026GS floor votes -> *_recovered.csv
python3 ut_state/db/build_db.py                         # CSVs -> ut_state.db (standard schema)
# advisory_opinions / statutes / projections refresh per their own SOURCES.md (Wayback CDX,
# le.utah.gov chapter XML, Gardner cloudfront workbooks respectively)
python3 scripts/build_cities_db.py                     # federation — run by the integrator, NOT here
```
