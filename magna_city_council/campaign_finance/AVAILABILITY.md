# Magna — Campaign-Finance Disclosures: Availability

**As-of:** 2026-07-13 · **Layer:** ACQUISITION-ONLY (raw filings retained; no dollar totals
computed — OCR/vision extraction deferred). **Cycles in scope:** township 2016(founding) /
2017 / 2019 / 2021 / 2023 + the **2025 first city-era election** (Magna's first directly-elected
Mayor).

Magna is a Salt Lake County **metro township (2017–2025) → city (2024-05-01, HB35; first city
election 2025-11-04)**. Its elections are administered by the **Salt Lake County Clerk**, so the
finance record splits cleanly by era — and, unlike Kearns, **BOTH ends were reachable**: the
county static archive for the township years AND the city site for 2025.

| Cycle | Era | Filing host | Retrieved? |
|---|---|---|---|
| 2016 (founding) | metro township | SLCo Clerk **static** metro-township-councils archive | **YES — 38 PDFs** |
| 2017 | metro township | SLCo Clerk static archive | **YES — 2 PDFs** |
| 2019 | metro township | SLCo Clerk static archive | **YES — 4 PDFs** |
| 2021 | metro township | SLCo Clerk static archive | **YES — 6 PDFs** |
| **2023** | metro township | SLCo **EasyVote** portal (2022+) | **NO — SPA HTTP-500/auth-gated** |
| **2025** | **city** | **magna.utah.gov** DocumentCenter | **YES — 13 files (city site reachable)** |

**63 filings/artifacts retrieved** (50 township from the county static archive; 13 city-era from
the Magna city site). The only gap is **2023 (D1/D3/D5)**, blocked on the EasyVote SPA. This is a
markedly fuller yield than the sibling Kearns build (which lost both 2023 AND 2025 to portal
blocks) — **the difference is that magna.utah.gov is NOT Cloudflare-blocked** (browser-UA GET
returns HTTP 200), so the 2025 city-era filings, which for Kearns live only behind Cloudflare,
were fully retrievable here.

## What was checked (search order — SKILL §6, metro-township cluster order)

1. **SLCo Clerk static metro-township-councils archive — the township yield (2016–2021).**
   `saltlakecounty.gov/clerk/elections/financial-disclosures/metro-township-councils/` (HTTP 200)
   lists per-candidate PDF links grouped under **"Magna Metro Township → Metro Township Council
   1–5"**. Anchors were read directly (never guessed). **50 Magna-attributed PDFs** harvested
   (`/globalassets/…/financial_disclosure/…pdf`). It holds **2016–2021 only** (the county moved
   2022+ filing to EasyVote). Every file is a **scanned "_redacted" image PDF** (`format=scanned`),
   except the 2019 Pierce form which carries a born-digital template text layer.
2. **magna.utah.gov city elections page (2025 city-era) — the city-era yield.**
   `magna.utah.gov/161/Elections` (HTTP 200, **reachable**) hosts the 2025 record under two headings:
   - **"Magna Primary Election Campaign Financial Disclosures"** → **9 per-candidate PDFs**
     (`/DocumentCenter/View/<id>/Magna---<Name>`): Mayor **Sudbury, Adriano, Romero, White**;
     D2 **Olsen, Barney, Rodriguez**; D4 **George, Hull**.
   - **"Magna General Election Campaign Finance Disclosure"** → **3 multi-candidate BUNDLE PDFs**:
     `Magna-Oct-7…` (v642), `Magna-Oct-28…` (v643), and `Magna-Primary-Eliminated…` (v644).
   - Plus **`Magna-2025-Election-Candidates-Conflict-of-Interest-Form`** (v533, 33 pp born-digital)
     → indexed as a `filing_type=coi_disclosure` row (SKILL: COI note → coi_disclosure).
   The **certified candidate list** (v524) was fetched as roster context (not an index row) and
   OCR-read to map candidates → races.
3. **SLCo EasyVote portal (2022+)** — `ecf-api.easyvoteapp.com/authentication/getwebsiteuser/saltlakecountyut`
   returns **HTTP 500** to a polite GET (same auth/reCAPTCHA gate the Kearns build documented). Under
   GET-only, no-POST, no-reCAPTCHA-bypass rules the portal is unreachable → **2023 D1/D3/D5 township
   filings could not be retrieved** (`unrecovered.csv`).
4. **State `disclosures.utah.gov/Municipal` (long-shot; metro-township cluster lesson).** The Salt
   Lake municipal page (HTTP 200) contains **zero "magna" occurrences** — Magna, like the other
   metro-township-origin entities (Kearns/White City/Copperton/Emigration), is **absent from the
   state tree**. The state hosts no Magna PDFs.
5. **Wayback Machine** (`web.archive.org` CDX) — **0 captures** for
   `saltlakecounty.gov/globalassets*magna*` beyond the pre-2022 static set; no archived 2022–2025
   Magna disclosure PDFs. 2023 is not recoverable via Wayback either.

## Coverage vs the election roster (`election_results/magna_races.csv`)

| Cycle | Contest(s) | Certified winners/runners | Finance filings held | Status |
|---|---|---|---|---|
| 2016 (founding) | Seats 1–5 | Prokopis/York, Peel/Elieson, Peay/Gardner, Hull/J.Sudbury, Ferguson/(Nosack) | **38** | Founding cycle: all 5 seat winners + all runners-up captured, + the full primary field |
| 2017 | Seats 2 & 4 | Peel (unc.), Hull (unc.) | **2** | Both uncontested winners captured |
| 2019 | Districts 1/3/5 | Prokopis (unc.), Peay (unc.), Pierce (unc.) | **4** | All three winners captured (Peay filed interim + Dec summary) |
| 2021 | Districts 2 & 4 | Barney/Peel, Hull (unc.) | **6** | Winner + runner-up + 3rd candidate (Ramos) all captured |
| **2023** | Districts 1/3/5 | *absent from election layer* | **0** | **GAP — EasyVote SPA HTTP-500/auth-gated** (see below + `unrecovered.csv`) |
| **2025** | Mayor + D2 + D4 | Sudbury/Adriano, Olsen/Barney, George/Hull | **13** | **All 10 candidates covered** (9 per-candidate primary + bundles; see note) |

**2016–2021 township coverage is effectively complete** for the retrievable (pre-EasyVote) era:
every certified winner and runner-up filed and is captured, plus the 2016 primary field.
**2025 city coverage is complete at the candidate level:** the 4 Mayor + 3 D2 + 3 D4 candidates
(10 total) are all present — 9 as per-candidate primary disclosures; the 10th, **Brooks Jones (D4,
eliminated at the primary)**, has **no per-candidate PDF** but is covered inside the
`primary-eliminated` bundle (v644) alongside the other eliminated candidates (Romero, M. White,
Rodriguez). The two general bundles (Oct-7 / Oct-28) hold the six finalists' general-period reports.
**2023 is the sole cycle with no filings** — a documented technical-access gap, not "nothing filed."

## Bundles — one artifact = one index row (per-candidate split deferred)

Three 2025 files are **multi-candidate bundles** (the city posted the general-election and
primary-eliminated disclosures grouped into single PDFs). Each is indexed as **one row per PDF**
(candidate = a bundle label; the contained candidates are named in the row `notes` and above),
because a reliable per-candidate split requires reading every page — and the bundles are **mixed
born-digital + scanned per page** (`pdftotext` recovers only the born-digital pages). Per-candidate
attribution and dollar figures belong to the deferred `/cf-vision-transcribe` → `cycle_totals.py`
pass. **Do NOT treat a bundle row as a single candidate's total.**

## Threshold-exemption / dollar reality

- **Not computed here.** No contribution/expenditure dollar figure is asserted in this layer.
- **Small-Budget exemption is live for this entity.** The SLCo Clerk allows a **Small Budget
  Campaign Certificate** for campaigns under **$2,000** (then only a general + year-end report is
  required). Magna township races are small (2021 D2 general = 581 votes; several uncontested), so
  some retrieved filings may themselves be small-budget certificates, and some 2023 candidates
  (esp. uncontested seats) may be threshold-exempt with little or nothing to file even if EasyVote
  were reachable. Recorded as a caveat, not asserted per-candidate.

## Double-count / dedup (SKILL §6 — the trap)

`is_incremental` is left **BLANK** on every row — classifying cumulative-vs-incremental requires the
deferred extraction pass. Utah convention: the **December year-end summary** (`filing_type=summary`,
5 rows: Peay 2019, Barney/Peel/Hull 2021) is the cumulative cycle total; the interims are period
reports. **Do NOT sum a candidate's filings**, and **do NOT sum a bundle row**. Any per-candidate /
per-cycle dollar total MUST go through `scripts/campaign_finance/cycle_totals.py`, never a raw row sum.

## Year attribution — OCR-verified, not guessed (a build note)

The county static page shows only a **month** per link, not a year; the 2016 cohort is fixed by the
`/2016_disclosures/<month>/` path, but the 12 root-level (2017/2019/2021) files carry no year in the
URL. Each root file's year was read from its printed **"&lt;YYYY&gt; Financial Disclosure For a Metro
Township Candidate"** header via `tesseract` OCR of page 1. This **corrected three initial
path-label guesses**: `brint-peel-magna.pdf`, `trish-hull--magna-4.pdf`, and `trish-hull-magna.pdf`
are all **2021** (not 2017) — Peel's 2021 D2 runner-up filing and Hull's 2021 D4 filings. Files were
renamed to their verified year and the `_fetch_log.jsonl` `saved_as` synced. `date_precision =
county_month_label_year_ocr` marks these; `county_folder_ym` marks the 2016 path-dated files;
`city_*` marks the 2025 city rows.

## Discrepancy FLAGS (recorded here only — do NOT edit `election_results/`)

1. **The 2023 D1/D3/D5 cycle is a DOUBLE gap.** It is missing from BOTH the finance record (EasyVote
   blocked) AND the election layer (`magna_races.csv` has **no 2023 Magna rows** — the pre-existing
   D1/D3/D5 archive gap the recon flagged, distinct from this dataset). Finance cannot fill it here.
   The 2023 candidates in `unrecovered.csv` are **inferred from the 2026 roster** (Prokopis D1,
   Pierce D5; Jensen holds D3 by 2026 after Peay), **not certified**. Recoverable later via a
   browser/session fetch of EasyVote. **No election contest is contradicted.**
2. **No finance-surfaced phantom candidate.** Unlike the Kearns build (a 2019 Geertsen filing with no
   matching certified contest), **every retrieved Magna filing maps to a candidate of record** for a
   plausible cycle — no finance filing surfaces a candidate the election layer omits. Nothing to
   reconcile.
3. **Water-District decoys excluded.** The dominant "MAGNA" election rows are the **Magna Water
   District** (a separate special district) + Magna MSD + the 2015 incorporation/MSD ballot
   questions. The county metro-township-councils archive is candidate-scoped to the Council seats, so
   **no water-district filing appears** here; none was ingested. (Only the council/mayor candidate
   filings were harvested.)
4. **These are campaign finance + one COI packet.** 62 rows are candidate contribution/expenditure
   disclosures; **1 row is the 2025 candidate conflict-of-interest packet** (`filing_type=
   coi_disclosure`, Utah Code 10-3-1301) — retained because the city site (unlike Kearns's) was
   reachable. A separate sitting-official "Disclosure Statements" page (`/170`) exists and is
   reachable but was not harvested (out of candidate-finance scope; note for a future pass).

## Formats

- **Scanned (`format=scanned`, 56 rows):** every SLCo "_redacted" county PDF (49 of 50) and 7 of the
  2025 per-candidate scans. `pdftotext -layout` yields ~0 characters.
- **Text/born-digital (`format=text`, 7 rows):** the 2019 Pierce form (template text layer); the 2025
  Barney + Maxwell White primary PDFs; the 3 bundles (mixed — text on the born-digital pages); and the
  COI packet. `extraction_method = "none (raw acquisition; text/OCR/vision deferred)"` on **every**
  row regardless — this layer computes no dollar totals.

## Honest gaps / non-issues

- **2016 is the founding township cycle** — below the repo's 2017 data floor, but the elections layer
  covers 2016 and these founders overlap the later roster (Prokopis, Peel, Peay, Hull, Ferguson), so
  the 38 founding-cycle filings are **retained as valid context** (clearly labeled `election_year=2016`).
- **2023 (metro township):** blocked by EasyVote SPA HTTP-500/auth-gate — `unrecovered.csv` (3 offices).
- **No standalone COI harvest beyond the candidate packet** — the sitting-official Disclosure Statements
  page was not pulled (scope).

## 2026-07-18 — Structured money layer built (dollar totals now computed for 13 filings)

The deferred dollar-extraction pass ran: `build_finance.py` (family `vision_cache`) structured
the **13** vision-cached filings (2021 township ×6 + 2025 city ×7) into
`contributions.csv`/`expenditures.csv`/`filing_totals.csv`/`cycle_totals.csv`. The other **49**
in-scope index rows are honest **inventory-only** rows (unknown totals + a dated reason); the
**COI packet** is out of scope; **2023** remains an EasyVote acquisition gap (`unrecovered.csv`).
`validate_finance.py` PASS. **Read `cycle_totals.csv` for any per-candidate/race total — never
sum `filing_totals`.**

- **Cover totals EXCLUDE in-kind** on Magna's forms (verified Romero/Olsen) → the build
  reconciles cash rows only.
- **Verbatim reconcile flags (never corrected):** Olsen $2.00 (both sides), Sudbury $100.00
  (expenditures). Ramos 2021 "Less than $1,000.00" is a threshold cert → recorded UNKNOWN.
## 2026-07-19 — GENERAL-BUNDLE PER-CANDIDATE SPLIT DONE (the follow-up above, closed)

The 3 multi-candidate 2025 bundles (v642 Oct-7, v643 Oct-28, v644 primary-eliminated) **and** the
clean Maxwell White v571 report were **vision-transcribed** (Read tool, **$0 API**; 3 chunk agents,
~78 page-images) into per-candidate `reports:[...]` caches (489b0ca5 / 8586d25d / 0a3cfc7e) + the
White single cache (8f3ed514). `build_finance.py` now **EXPANDS** each bundle into per-candidate
filings (via a scratchpad expanded-index handed to the shared engine — the acquisition `index.csv`
stays one row per bundle). Results: `filing_totals` **62→73 rows**, both-sides-reconcile **5→16**,
contributions **23→74**, expenditures **40→108**; `validate_finance` PASS, `validate_city` 0 FAIL.

2025 cycle totals now include the GENERAL-ELECTION period (`cycle_totals.csv`):
Sudbury **$9,735 spent** / Adriano **$4,222** (Mayor); Olsen **$2,790** / Barney **$431** (D2);
George **$1,982** / Hull **$191** (D4); Romero **$1,259**; White **$20**. The forms' cumulative
Column-A/C quirks surface as honest reconcile FLAGS (kept verbatim); the correct WHOLE-CYCLE
figures for Sudbury / Adriano / Romero (which the generic dedup can't derive from the mixed
columns) are set from each candidate's own BALANCE CHAIN via **`cycle_overrides.csv`** (3 rows,
per-candidate evidence). **Do NOT sum `filing_totals` — read `cycle_totals.csv`.**

- **Brooks Jones (2025 D4, primary-eliminated) — NOW STRUCTURED (2026-07-19):** his section of
  the v644 bundle ($958.44 self-funded) had **no acquisition `index.csv` row** (he never filed a
  per-candidate PDF), so structuring it would have failed `validate_finance` (candidate ∉ index).
  Resolved by adding an honest **membership** index row for him (same v644 bundle artifact — identical
  path/source_url/sha256, generated by `build_magna_cf_index.py`'s `BUNDLE_MEMBERS`) and setting his
  `vision/0a3cfc7e.json` `candidate_canonical` to "Brooks Jones"; he now auto-structures from the
  cache — **$958.44 raised / $958.44 spent, both sides reconcile** (verbatim from the cache, not
  fabricated). Jones-only change; `validate_finance` PASS. See `CLAUDE.md` for the design note.
- **Still a vision follow-up:** the 2016–2019 township scans + the 2019 Pierce / 2025 Barney
  handwriting-template text layers (real money, not machine-readable). 2023 stays an EasyVote gap.
