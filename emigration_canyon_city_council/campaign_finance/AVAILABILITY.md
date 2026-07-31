# Emigration Canyon — Campaign-Finance Disclosures: Availability

**As-of:** 2026-07-14 · **Layer:** ACQUISITION-ONLY (raw filings retained; no dollar totals
computed — OCR/vision extraction deferred). **Cycles in scope:** township founding **2016** /
**2017** (@LRG) / **2019** + the city-era **2025** first-city-election candidate filings, plus
current elected-officer Conflict-of-Interest forms.

Emigration Canyon is a Salt Lake County **metro township (2017–2024) → CITY (2024-05-01, HB35)**,
~1,600 residents, MSD-staffed, **no city document CMS** (a minimal Wix site + PMN only). Elections
are administered by the **Salt Lake County Clerk**, so the finance record splits by era exactly
like the sibling metro-township cluster (Copperton/Kearns/Magna/White City).

> ⚠ **The task premise that candidates were "almost certainly threshold-EXEMPT → honest
> near-empty" turned out to be only PARTLY true** — the same lesson as Copperton. The SLCo Clerk
> static archive holds a **real, non-trivial yield of 26 candidate campaign-finance filings**
> (2016/2017/2019), and the **city Wix site posts 4 genuine 2025 candidate campaign-finance
> statements** (they filed the Report of Contributions and Expenditures, even the low-vote
> primary also-rans). The honest-empty / blocked part is real only for **2023** (EasyVote
> portal-blocked) and the **2025 GENERAL-election reports** (only the primary report is posted).

| Cycle | Era | Filing host | Retrieved? |
|---|---|---|---|
| 2016 (founding) | metro township | SLCo Clerk **static** metro-township-councils archive | **YES — 16 PDFs (8 candidates)** |
| 2017 (@LRG) | metro township | SLCo Clerk static archive | **YES — 4 PDFs (Smolka, Bowen)** |
| 2019 | metro township | SLCo Clerk static archive | **YES — 6 PDFs (Hawkes, Brems, Tippetts, Harris)** |
| **2023** | metro township | SLCo **EasyVote** portal (2022+) | **NO — SPA HTTP-500/auth-gated** (`unrecovered.csv`) |
| **2025 (city) — primary CF** | city | emigration.utah.gov `/election-information` | **YES — 4 PDFs (Pinon, Steed, Posner, Wheelock)** |
| **2025 (city) — general CF** | city | emigration.utah.gov | **NO — only the Aug-5 primary report posted** (`unrecovered.csv`) |
| Current elected-officer COI forms | city | emigration.utah.gov `/copy-of-disclosure-statements` | **YES — 5 COI PDFs** |

**35 index rows** = **30 candidate campaign-finance filings** (26 SLCo static 2016–2019 + 4 city
2025 primary) + **5 Conflict-of-Interest disclosures** (`filing_type=coi_disclosure`, current
elected officers). **29 scanned / 6 born-digital-text.** No dollar figure is asserted in this layer.
(A 36th fetched PDF — `raw/_context_2017_township_budget_NOT-cf.pdf`, an unlabeled link on the
`/disclosure-statements` page — turned out to be a **2017 township budget spreadsheet**, NOT a
finance filing, so it is retained as context and **not indexed**.)

## What was checked (SKILL §6 search order — the metro-township cluster order)

1. **SLCo Clerk static metro-township-councils archive — the PRIMARY yield.**
   `saltlakecounty.gov/clerk/elections/financial-disclosures/metro-township-councils/` (HTTP 200)
   lists per-candidate PDF links under an **"Emigration Canyon Township / Emigration Township
   Council At Large"** section. **26 Emigration-attributed PDFs** were harvested (anchors read
   directly off the rendered HTML, never guessed; saved page = `raw/_slco_metro_township_archive.html`).
   The page groups each PDF under an explicit **candidate header ("Last, First")** and a
   **year header ("&lt;YYYY&gt; Financial Disclosure Reporting")**, so the election_year is read
   from the COUNTY PAGE structure itself (`date_precision=county_page_year_label`; the 2016 files
   also carry the year in their `/2016_disclosures/…` URL path → `county_folder_ym`) — this is
   MORE reliable than the Copperton build, which had to OCR each form's title line. The page holds
   **2016–2019 only** (the county moved 2022+ filing to EasyVote). Almost every file is a **scanned
   image PDF** (`format=scanned`, `pdftotext` ~0 chars).
2. **City of Emigration Canyon Wix site (`emigration.utah.gov`, HTTP 200).**
   - `/election-information` posts the **four 2025 candidates' campaign-finance statements** —
     "City of Emigration Canyon Municipal Elections · Campaign Finance Statement · Report of
     Contributions and Expenditures (Utah Code 10-3-208)", type-of-report box = **"All Primary
     Election Candidates — DUE Aug 5, 2025"**. Pinon's is a born-digital fillable PDF (text);
     Wheelock/Steed/Posner are scanned images. **Only the primary report is posted** — the same
     form's Oct-7 / Oct-28 / Dec-4 general-election boxes are unchecked and no later reports appear.
   - `/copy-of-disclosure-statements` posts the **current elected officers' Conflict-of-Interest
     forms** (Brems/Mayor, Hawkes, Harris, Pinon — "ELECTED OFFICER CONFLICT OF INTEREST
     DISCLOSURE", Utah Code 10-3-1301; plus Griffith on the candidate/officeholder 10-3-1313 form).
     These are `filing_type=coi_disclosure`, NOT campaign-finance dollar reports.
   - `/disclosure-statements` (an older/parallel page) held only study PDFs + one unlabeled link
     that resolved to a **2017 township budget spreadsheet** (not finance → context-only).
   - Docs live at Wix `emigration.utah.gov/_files/ugd/e1a144_<hash>.pdf` (hashes harvested from the
     rendered anchors).
3. **SLCo EasyVote portal (2022+).**
   `ecf-api.easyvoteapp.com/authentication/getwebsiteuser/saltlakecountyut` returns **HTTP 500** to
   a polite GET (the same reCAPTCHA/auth gate the Copperton/Kearns/Magna builds documented). Under
   GET-only, no-POST, no-reCAPTCHA-bypass rules the portal is unreachable → **2023 metro-township
   filings could not be retrieved** (`unrecovered.csv`).
4. **State `disclosures.utah.gov`.** Root HTTP 200 but `Search/AdvancedSearch` returns **HTTP 500**;
   the metro-township-origin entities are historically **absent** from the state Municipal tree
   (the cluster lesson). No Emigration PDFs expected or found there.
5. **MSD site** (`msd.utah.gov/349/Emigration-Canyon`, HTTP 200) — a community/AgendaCenter mirror
   with **no campaign-finance or disclosure links**. **Wayback** was not needed (the county static
   archive + the city site were both directly reachable); the 2023 EasyVote gap is not
   Wayback-recoverable (dynamic SPA).

## Coverage vs the election roster (`election_results/emigration_canyon_races.csv`)

| Cycle | Council contest / candidates | CF filings held | Status |
|---|---|---|---|
| **2016 (founding)** | founding at-large council — Hawkes, Hook, Staggers, Smolka, Bowen, Brems, Raile, Christensen | **16** (8 cand × interim + summary/dissolution) | *Founding contest ABSENT from election_results (labeled 2017 there) — flag #1* |
| **2017 (@LRG)** | vote-for-2 at-large — Smolka (W), Bowen (W) | **4** (both winners, interim + summary) | Both 2017 @LRG winners captured |
| **2019** | Hawkes, Brems, Tippetts, Harris | **6** | *2019 contest ABSENT from election_results AND recon §6 said "no 2019 council contest" — finance CONTRADICTS that (flag #2)* |
| **2023** | Harris (W), Hawkes (W), Brems (W), Tippetts (L) | **0** | **GAP — EasyVote SPA HTTP-500/auth-gated** (`unrecovered.csv`) |
| **2025 (city) — primary** | Pinon (W), Steed, Posner, Wheelock (all 4 named primary candidates) | **4** | **Full primary field captured** (they DID file — not exempt) |
| **2025 (city) — general** | Pinon (W), Steed (L) | **0** | **GAP — only the Aug-5 primary report is posted** (`unrecovered.csv`) |
| current officers (COI) | Brems, Hawkes, Harris, Pinon, Griffith | **5 COI** | Annual ethics COI (10-3-1301/1313), not CF |

**2016–2019 township coverage is effectively complete for the retrievable (pre-EasyVote) era**, and
the **entire 2025 primary field filed and is captured.** **2023 is the sole campaign-finance cycle
with no filings** (EasyVote technical-access gap, not "nothing filed"), and only the 2025 *primary*
(not *general*) reports are on the city site.

## Discrepancy FLAGS (recorded here only — do NOT edit `election_results/` or `roster/`)

1. **Founding-cycle: finance shows a broad 2016 founding field; the election layer labels the
   founding contest 2017 and preserves only Smolka + Bowen.** Eight candidates (Hawkes, Hook,
   Staggers, Smolka, Bowen, Brems, Raile, Christensen) filed **2016** founding metro-township
   council disclosures (county page "Emigration Township Council At Large / 2016 Financial
   Disclosure Reporting"; the 2016 files also sit in the county's `/2016_disclosures/` path).
   `emigration_canyon_races.csv` dates/labels the founding @LRG contest **2017** and keeps only the
   two @LRG winners. So the finance record dates the founding cycle a year earlier and preserves a
   broader field. Metro-township founding elections were held **Nov 2016** (terms began 2017-01-01)
   — consistent with the 2016 filings. **Flagged, not reconciled.**
2. **A 2019 cycle is present in finance but ABSENT from the election layer — directly contradicting
   recon §6's "no Township council contest in 2019 or 2021."** Hawkes, Brems, Tippetts, and Harris
   each filed **2019** Emigration Township Council disclosures (county page "2019 Financial
   Disclosure Reporting"; interim + December summary for Tippetts/Harris, interim for Hawkes/Brems).
   `emigration_canyon_races.csv` has **no 2019 Emigration council rows**. This is the documented
   "2019 SLCo county-archive drop" seen for Copperton / South Jordan / Millcreek / Taylorsville —
   finance **confirms 2019 candidacy/campaign activity** for these four (all later the 2023
   winners/runner-up). It does not contradict any existing election row; it fills a known hole.
   `join_confidence=medium`. **Do not edit the election dataset** — re-parse the raw 2019 SLCo SOVC
   if the election layer is ever extended.
3. **Griffith holds a 2026 council seat but is NOT a certified 2025 candidate → appointed, not
   elected.** The current-officer COI set includes **Nicholas Griffith** (on the
   candidate/officeholder 10-3-1313 form), yet the certified 2025 candidate field was
   **Pinon/Steed/Posner/Wheelock** only (`emigration_canyon_races.csv` 2025 primary). Griffith is
   therefore an **appointee** to a seat that turned over (recon flagged "reconcile Griffith vs 2023
   winner Tyler Tippetts") — the COI record surfaces the roster nuance. **Flagged for the roster
   layer; not edited here.**

## Threshold-exemption / dollar reality

- **Not computed here.** No contribution/expenditure dollar figure is asserted in this layer
  (`extraction_method = none (raw acquisition; text/OCR/vision deferred)` on every row).
- **Candidates DID file.** Contrary to the "almost certainly threshold-exempt / honest-empty"
  premise, the county archive holds 26 township filings and all four 2025 primary candidates filed
  the city's Report of Contributions and Expenditures (even the 14-vote and 53-vote also-rans). The
  Utah **Small Budget Campaign Certificate** (< $2,000) exemption is live for a jurisdiction this
  size, so some filings may themselves be small-budget certificates or report near-$0 — recorded as
  a caveat, not asserted per-candidate. The genuine honest-empty/blocked cycles are **2023** (portal)
  and the **2025 general-election reports** (not posted).

## Double-count / dedup (SKILL §6 — the trap)

`is_incremental` is left **BLANK** on every row — classifying cumulative-vs-incremental requires the
deferred extraction pass. Utah convention: the **December year-end `summary`** is the cumulative
cycle total; the Oct/Nov `interim` reports are period reports; **dissolution** reports (2016
`summary`, county `/dissolutions/` folder) close a committee. **Do NOT sum a candidate's filings.**
Any per-candidate / per-cycle dollar total MUST go through `scripts/campaign_finance/cycle_totals.py`,
never a raw row sum. The 5 COI rows carry no dollars at all.

## Formats

- **Scanned (`format=scanned`, 29 rows):** all 26 SLCo county PDFs (`pdftotext` ~0 chars) + the 3
  scanned 2025 city CF forms (Wheelock/Steed/Posner — image scans, ~28–29 chars).
- **Text/born-digital (`format=text`, 6 rows):** Pinon's 2025 CF (born-digital fillable PDF) + the
  5 city COI forms (scanned filled forms that carry an embedded/OCR text layer → pdftotext yields
  2.7–3.9k chars). `extraction_method` is uniform `none (raw acquisition; text/OCR/vision deferred)`
  regardless — this layer computes no dollar totals.

## Honest gaps / non-issues

- **2016 is the founding township cycle** — the founders overlap the later roster (Smolka, Bowen,
  Hawkes, Brems, Harris), so the 16 founding filings are retained as valid context (`election_year=2016`).
- **2023 (metro township):** blocked by the EasyVote SPA HTTP-500/auth-gate — `unrecovered.csv`
  (3 winners + 1 runner-up).
- **2025 general-election CF:** only the Aug-5 primary report is posted per candidate — the Oct/Dec
  general reports are not on the city site (`unrecovered.csv`, Pinon + Steed).
- **COI vs campaign finance:** the 5 `coi_disclosure` rows are conflict-of-interest statements
  (10-3-1301 / 10-3-1313), retained per the SKILL's COI→coi_disclosure note; they are **not**
  contribution/expenditure reports and carry no dollar figures.
- **Improvement-District decoy:** none entered this dataset. The county's own section header files
  every retrieved PDF under the **township council**, not the Emigration Canyon Improvement District
  (a separate sewer/water special district) — recon §6's decoy warning is respected.

## 2026-07-17 — STRUCTURED DOLLAR LAYER BUILT (supersedes the "no dollar totals computed" premise)

The deferred dollar-extraction pass is DONE. `build_finance.py` (family `vision_cache`) now emits
`contributions.csv` (16) / `expenditures.csv` (16) / `filing_totals.csv` (30) / `cycle_totals.csv` (18);
`validate_finance.py` PASS (0 fail, 5 warn = the excluded COI rows). All 30 in-scope C&E filings are
transcribed — the 29 scanned via the pre-staged vision caches + Pinon 2025 from its born-digital text.

**Dollar reality confirmed:** the "almost-certainly threshold-exempt / near-empty" premise is now
QUANTIFIED — the record is overwhelmingly **$50 filing-fee-only, self-funded** and zero-activity
filings. Real money appears in exactly one cycle: **Brems 2016** raised/spent **$662.11** (incl. a
$245.69 Bradley contribution). Everyone else's cycle total is **$50 or $0**. **Read `cycle_totals.csv`,
never sum `filing_totals`** — the per-candidate regime dedup is encoded there (no `cycle_overrides.csv`
needed; zero review flags).

**Gaps unchanged:** 2023 (EasyVote-blocked) and the 2025 general-election reports (only the Aug-5
primary posted) remain in `unrecovered.csv` — no filings exist to structure. The 5 COI forms carry no
dollars and are excluded from the money layer.

**Verbatim quirks flagged, never corrected** (see the CF `CLAUDE.md` dated section for the full list):
Brems-2016 $100 cover-vs-items arithmetic error (`reconciles_expend=False`); 2019 Harris/Hawkes −$50
ending balances; 2019 Tippets Dec cover-page-only nulls; 10 totals-only filings reconcile UNKNOWN.
**Bowen 2016** — the November PDF two-report bundle (June 21 + November 1 stapled) was re-visioned into
the `reports[]` schema so its $55 cycle is captured (was heading to $0).
