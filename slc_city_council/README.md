# SLC City Council — data repository

A civic-data repository for the **Salt Lake City Council** (Salt Lake County, Utah) —
the **original city** the 12 clone repos and the `build-city-data-repo` skill were
modeled on. Council/agency minutes as markdown, extracted roll-call votes, weekly
public-comment PDFs as a cleaned dataset, municipal election results, and an
address→district geo tool, covering **2020–present**. See `CLAUDE.md` for analysis
guidance; sources map in `recon.md` (retrospective); QA + the 2026-07-02
standardization retrofit in `VERIFICATION.md`.

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Meeting minutes | 2020-01-07 → 2026-06-09 | 457 documents | PrimeGov (`slc.primegov.com`) 2021+; Laserfiche (`webdme.slcgov.com`) 2020 | ✅ 389 Markdown (text) + 68 OCR |
| Roll-call votes | 2021-01-05 → 2026-06-09 | 1,842 motions · 12,840 rows | LLM-extracted from the clean 2021+ minutes | ✅ audited A; ~4% contested |
| — by body | | Council 10,528 · RDA 1,485 · CRA 556 · LBA 271 rows | in-session body transitions, walked from section headers | ✅ `body` column (retrofit 2026-07-02) |
| **Planning Commission** | 2020–2026 | 145 meetings · 740 motions · 5,333 rows | PrimeGov (same portal), pure-regex extraction | ✅ `planning_commission/` (body=PlanningCommission) |
| — PC stages | | 252 recommendations (211+/41−) · 290 final actions · 198 procedural | recommendation vs final-action taxonomy | ✅ 30 rostered commissioners |
| **Relational database** | 2020–2026 | 2,582 motions · 18,169 votes · **31 PC/agency→Council referrals** | derived from the vote CSVs | ✅ `db/civic.db` + `db/tables/*.csv` — start at `db/SCHEMA.md` |
| Public comments | 2020–2026 | **13,334** cleaned comments (1,654 dropped w/ audit trail) | slcdocs.com weekly PDFs → Claude Vision | ✅ audited A−; refresh via `/check-slc-comments` |
| Election results | 2007–2025 | 57 SLC races (18 raw county files) | Salt Lake County municipal results | ✅ raw CSVs retained as source of truth |
| Geo (district mapper) | current | 144 SLC precincts → 7 districts | county precinct boundaries + election-derived lookup | ✅ `geo/address_to_district.py` |
| Weekly bundles | 2020–2026 | 327 weeks | derived (`build_weeks.py`) | ✅ regenerable |

## Council structure

**Mayor + 7 councilmembers in geographic districts**, staggered 4-year terms (odd
districts 1/3/5/7 elected 2009/13/17/21/25; even 2/4/6 in 2007/11/15/19/23). The Mayor
is elected separately (strong-mayor form) and does not vote with the Council. The
council meets **Tuesdays**; the whole repo keys on the council week ending that Tuesday.

## The four in-session bodies (SLC quirk)

The Council adjourns/reconvenes **in-session** as the **RDA** (Redevelopment Agency),
**CRA** (Community Reinvestment Agency), and **LBA** (Local Building Authority), so one
minutes document interleaves up to four bodies. `meeting_minutes/all_votes.csv` carries
a per-row `body` column (Council/RDA/CRA/LBA — clone-standard short codes), derived by
walking the minutes' section headers; `db/civic.db` stores the same derivation under
full body names.

## Planning Commission + relational database (cross-body analysis)

`planning_commission/` mirrors `meeting_minutes/` for the appointed technical land-use
body (same 13-col vote schema, every row `body=PlanningCommission`; 277 motions
non-unanimous). The `result` string encodes **recommendations forwarded to Council**
(252 — 211 Positive / 41 Negative) vs **final actions** (290) vs procedural (198).

`db/civic.db` is the canonical queryable form — **prefer it for any cross-body or
project-level question** (the flat CSVs carry no keys). Built in two idempotent stages,
never conflated: `python3 db/build_db.py` (exact within-body core; project keys resolved
from prose, body-scoped) then `python3 db/build_referrals.py` (reconstructed cross-body
referral layer: 31 scored links — 11 high / 15 medium / 5 low; 28 Council←PC + 3
Council←agency). Start at `db/SCHEMA.md`.

## Public comments (rare among Utah cities)

The Council publishes written comments as weekly PDFs on slcdocs.com; extracted with
Claude Vision and cleaned into `public_comments/all_comments_clean.csv` (13,334 rows,
2020–2026; every dropped row logged with a reason). One of only two substantive
public-comment corpora in the collection. Incremental refresh:
`public_comments/check_new_comments.py` (wrapped by the `/check-slc-comments` skill).

## Elections + geo

Raw Salt Lake County municipal results (2007–2025 — far deeper than the clones' 2019+)
filtered/normalized to 57 SLC council+mayor races by `election_results/clean_elections.py`.
`geo/address_to_district.py` resolves any SLC address or lat/long to its council
district (Census geocode → precinct point-in-polygon → election-derived
precinct→district lookup), tying an address/comment to a district's member, votes,
and election margin.

## Known gaps & seams (honest)

- **Votes are 2021+ only** — the 2020 Laserfiche minutes are OCR, too messy for
  reliable roll-call extraction (the 68 files are kept as text).
- **68/457 minutes rows have no `source_url`** in `minutes_index.csv` (2020 Laserfiche);
  their per-document provenance (entry_id + DocView URL) is in
  `meeting_minutes/index_laserfiche.csv`.
- **~8 unrecoverable comment pages** (5 API content-filter blocks, 3 JSON edge cases) —
  documented in `public_comments/CLAUDE.md`; a handful of comments at most.
- Comments are weekly from ~2020-07 (earlier files are per meeting date); some
  summer-recess weeks legitimately have 0 comments.
- Raw minutes PDFs/HTML are not retained — re-fetchable via `minutes_index.csv`
  `source_url` (PrimeGov) and `index_laserfiche.csv` (Laserfiche).

## Regenerate

- Weekly bundles: `python3 build_weeks.py` (derived — safe to delete, never hand-edit)
- Comments: `python3 public_comments/clean_comments.py --report` (from raw JSON; no API cost)
- Votes: `python3 meeting_minutes/extract_votes.py` (resumable; needs `ANTHROPIC_API_KEY`)
- Elections: `python3 election_results/clean_elections.py --report`
- Database: `python3 db/build_db.py && python3 db/build_referrals.py` (idempotent)
- Minutes refresh: `python3 meeting_minutes/scrape_primegov.py` (rebuilds the standard
  `minutes_index.csv`; legacy extras frozen in `minutes_index_legacy.csv`)

---
*Rewritten 2026-07-02 to the clone-repo template (REMEDIATION_PLAN.md Phase 2.5); counts
carried from the Phase 1.8 doc sweep and re-verified. Prior README in
`_backups/2026-07-02/slc_city_council/README.md.pre-phase2.5`.*

## Expansion datasets (additive, 2026-07-06)
Six additional source layers (PrimeGov + slcdocs.com + Utah Public Notice + YouTube), each
documented in its own folder and in `EXPAND_SOURCES_REPORT.md`. None modify the core data.

- **`packets/`** — 582 Council + Planning Commission agenda packets (Council catalogued with live
  URLs, ~15–30 GB on the portal; recent PC packets stored). doc_class (2026-07-16): 11 PC-2026 staff
  reports classified (whole-class verified); Council packets ruled not separable (monolithic, index-only).
- **`housing_plans/`** — SLC's flagship housing plans: Growing SLC, Housing SLC, and Thriving in Place.
- **`ordinances/`** — 443 adopted ordinances (all Council), most matched to the adopting vote.
- **`pmn_backfill/`** — 7 recovered meetings, plus recovered citation URLs for 65 of the 68 2020
  minutes that previously had none.
- **`transcripts/`** — a 1,142-video map of meeting recordings + 10 sampled ASR caption tracks (YouTube).
- **`campaign_finance/`** — the city's disclosure portal was under maintenance during the build, so this
  dataset is an honest empty placeholder with a ready harvester to re-run once the portal is back.

The per-file source/citation index (`sources.csv` + `SOURCES.md`) covers all of the above.
