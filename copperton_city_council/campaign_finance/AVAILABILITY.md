# Copperton — Campaign-Finance Disclosures: Availability

**As-of:** 2026-07-14 (acquisition) · **2026-07-17** (STRUCTURED DOLLAR LAYER BUILT — see the
addendum at the bottom). **Layer:** the 19 scanned township C&E filings are now transcribed +
reconciled into `contributions.csv`/`expenditures.csv`/`filing_totals.csv`/`cycle_totals.csv`
(query `cycle_totals.csv` for any per-candidate total — never sum filings). **Cycles in scope:**
township 2016 (founding) / 2017 / 2019 / 2021 / 2023 + the **2025 first Town election** (first
directly-elected Mayor).

Copperton is a Salt Lake County **metro township (2017–2024) → TOWN (2024-05-01, HB35; first
town election 2025-11-04)**, ~800 residents — a **very small** jurisdiction. Elections are
administered by the **Salt Lake County Clerk**, so the finance record splits by era exactly like
the sibling metro-township cluster (Kearns/Magna). ⚠ **The town-brief premise that candidates
were "almost certainly threshold-exempt / honest near-empty" turned out to be only PARTLY true:**
the SLCo Clerk static archive holds a **real, non-trivial yield of 19 candidate campaign-finance
filings** across 2016–2021 (candidates DID file). The honest-empty part is real only for **2023**
(portal-blocked) and **2025 campaign finance** (unopposed candidates → nothing posted).

| Cycle | Era | Filing host | Retrieved? |
|---|---|---|---|
| 2016 (founding) | metro township | SLCo Clerk **static** metro-township-councils archive | **YES — 5 PDFs** |
| 2017 (@LRG / D-E) | metro township | SLCo Clerk static archive | **YES — 3 PDFs** |
| 2019 (A/B/C) | metro township | SLCo Clerk static archive | **YES — 5 PDFs** |
| 2021 (D/E) | metro township | SLCo Clerk static archive | **YES — 6 PDFs** |
| **2023 (A/B/C)** | metro township | SLCo **EasyVote** portal (2022+) | **NO — SPA HTTP-500/auth-gated** |
| **2025 (Town) — campaign finance** | town | copperton.utah.gov (town recorder) | **NO — none posted (unopposed → exempt)** |
| 2025/2026 — Conflict-of-Interest forms | town | copperton.utah.gov `/disclosures` + `/election-information` | **YES — 6 COI PDFs** |

**25 index rows** = **19 candidate campaign-finance filings** (all 2016–2021, SLCo static archive)
+ **6 Conflict-of-Interest disclosures** (`filing_type=coi_disclosure`; 1 = the 2025 candidate COI
packet, 5 = the 2026 annual sitting-official COIs). **20 scanned / 5 born-digital text.** No dollar
figure is asserted in this layer.

## What was checked (SKILL §6 search order — the metro-township cluster order)

1. **SLCo Clerk static metro-township-councils archive — the PRIMARY yield.**
   `saltlakecounty.gov/clerk/elections/financial-disclosures/metro-township-councils/` (HTTP 200)
   lists per-candidate PDF links under a **"Copperton Metro Township"** header. **19
   Copperton-attributed PDFs** were harvested (anchors read directly, never guessed;
   `/globalassets/…/financial_disclosure/…pdf`). The page holds **2016–2021 only** (the county
   moved 2022+ filing to EasyVote). Every file is a **scanned image PDF** (`format=scanned`);
   `pdftotext` yields ~0 characters.
2. **Copperton town site (GoDaddy; TLS cert-mismatch → `curl -k`).**
   - `copperton.utah.gov/election-information` (HTTP 200) posts the 2025 **Official Notice**,
     **UOCAVA notice**, **Certified Candidate List**, and a **"2025 Election Candidates Conflict
     of Interest"** packet. **No campaign-finance contribution/expenditure PDF is posted.**
   - `copperton.utah.gov/disclosures` (HTTP 200) states: *"To meet the legal requirements passed
     in HB 80 in 2024, the Conflict of Interest and Campaign Financial Disclosure forms for all
     declared candidates can now be accessed"* — but in practice hosts only **5 "2026 Conflict of
     Interest"** forms (Clayton, Stitzer, Bailey, McCalmon, Pratt) — annual sitting-official COI
     statements (Utah Code 10-3-1301). **The campaign-financial-disclosure half is not posted**
     (the 2025 candidates were unopposed / threshold-exempt).
   - The town docs live at opaque `img1.wsimg.com/blobby/go/07a53a68-…/downloads/<guid>/…pdf`
     GUIDs harvested from the rendered anchors (site GUID matches the minutes recon).
3. **SLCo EasyVote portal (2022+).** `ecf-api.easyvoteapp.com/authentication/getwebsiteuser/saltlakecountyut`
   returns **HTTP 500** to a polite GET (same reCAPTCHA/auth gate the Kearns + Magna builds
   documented). Under GET-only, no-POST, no-reCAPTCHA-bypass rules the portal is unreachable →
   **2023 Seat A/B/C township filings could not be retrieved** (`unrecovered.csv`).
4. **State `disclosures.utah.gov`.** The host returns **HTTP 500** (down at check time); the
   metro-township-origin entities are historically **absent** from the state Municipal tree
   (Kearns/Magna/White City cluster lesson). No Copperton PDFs expected or found there.
5. **Wayback Machine** — not needed for a positive recovery here (the county static archive and
   the town site were both directly reachable); the 2023 EasyVote gap is not Wayback-recoverable
   (dynamic SPA), matching the sibling builds.

## Coverage vs the election roster (`election_results/copperton_races.csv`)

| Cycle | Council contest(s) | Certified winners / runners | CF filings held | Status |
|---|---|---|---|---|
| **2016 (founding)** | founding at-large council (seat letters not certified) | *not in election layer* (see flag #1) | **5** | Founding cohort: Ron Patrick, Tessa Stitzer, Kathleen Bailey, JP Baxter, Sean Clayton |
| **2017 (@LRG / D-E)** | vote-for-2 at-large | Pazell (W), Severson (W), Baxter (L) | **3** | All three 2017 @LRG candidates captured |
| **2019 (A/B/C)** | seats A/B/C | *ABSENT from election layer* (flag #2) | **5** | Bailey, Stitzer, Clayton — interim + Dec summary each (Clayton summary only) |
| **2021 (D/E)** | Seat D + Seat E | Olsen (D, W); Severson (E write-in W) / R. Patrick (E, runner-up) | **6** | Seat D winner + Seat E winner + Seat E runner-up, interim + summary each |
| **2023 (A/B/C)** | Seat A/B/C (all unopposed) | Bailey (A), Clayton (B), Stitzer (C) | **0** | **GAP — EasyVote SPA HTTP-500/auth-gated** (`unrecovered.csv`); unopposed → possibly exempt |
| **2025 (Town)** | Mayor + Seat D (both unopposed); Seat C no candidate | Clayton (Mayor), McCalmon (Seat D) | **0 CF** (+ 1 COI packet) | **Honest empty for CF** — unopposed/threshold-exempt; only a COI packet posted |

**2016–2021 township coverage is effectively complete for the retrievable (pre-EasyVote) era:**
every certified winner and runner-up of record filed and is captured, plus the founding field and
the (election-layer-missing) 2019 cohort. **2023 is the sole campaign-finance cycle with no
filings** — a documented technical-access gap, not "nothing filed" — though the unopposed seats may
themselves be Small-Budget-exempt. **2025 has no campaign-finance PDF** because both certified
candidates ran unopposed.

## Discrepancy FLAGS (recorded here only — do NOT edit `election_results/` or `roster/`)

1. **Founding-cycle YEAR label: finance says 2016, the election layer says 2017.** The five
   founding-cohort filings live in the county's `/2016_disclosures/november/` path AND each form's
   own title line reads **"2016 Financial Disclosure Report"** (OCR-verified). But
   `copperton_races.csv` labels/dates the founding at-large contest **2017** (source file
   `2017-11-07-general-election-…`). So the finance record dates the founding cycle a year earlier
   than the election layer. Metro-township founding elections were held **Nov 2016** (terms began
   Jan 2017) — consistent with the 2016 filings. Also, the founding finance cohort (Patrick,
   Stitzer, Bailey, Baxter, Clayton) does **not** match the 2017 @LRG contest field (Pazell,
   Severson, Baxter) in `copperton_races.csv` — the founding all-seats field is broader than the
   single @LRG contest the county SOVC preserved. **Flagged, not reconciled.**
2. **The 2019 A/B/C cycle is present in finance but ABSENT from the election layer.** Kathleen
   Bailey, Tessa Stitzer, and Sean Clayton each filed **2019** disclosures (form titles OCR-read as
   "2019 Financial Disclosure Report"; interim + December summary). `copperton_races.csv` has **no
   2019 Copperton rows** — the documented "2019 county-archive drop" (same drop seen for South
   Jordan / Millcreek / Taylorsville). **Finance CONFIRMS the 2019 A/B/C contest occurred** with
   these three as candidates. Seat letters (A=Bailey, B=Clayton, C=Stitzer) are **inferred** from
   the same members' certified 2023 seats, not independently certified for 2019 → `join_confidence
   = medium`. This does not contradict any existing election row; it fills a known hole. **Do not
   edit the election dataset** — re-parse the raw 2019 SOVC if the election layer is ever extended.
3. **2025: Pratt was appointed, not elected; Seat C drew no candidates.** The town clerk's
   **Certified Candidate List** (June 2025; `raw/_context_2025_certified_candidate_list.pdf`) lists
   only **Mayor: Sean Clayton** and **Council At-Large Seat D: Linda Marie McCalmon** (both
   unopposed), and **"Council Member — At-Large Seat C … No Candidate Declarations."** Yet
   **Jonathan Pratt** holds a council seat in 2026 (he filed a 2026 annual COI). Since Pratt was
   NOT a certified 2025 candidate, he was **APPOINTED** to the vacant seat, not elected. The recon
   / roster framing ("Pratt, new 2025, succeeds Severson, Seat E") should be read as an
   **appointment** to a **no-candidate seat labeled C** (not E) — a nuance the finance/COI record
   surfaces. **Flagged for the roster layer; not edited here.**

## Threshold-exemption / dollar reality

- **Not computed here.** No contribution/expenditure dollar figure is asserted in this layer.
- **Small-Budget exemption is live for this entity.** The SLCo Clerk allows a **Small Budget
  Campaign Certificate** for campaigns under **$2,000** (then only a general + year-end report is
  required). Copperton council races are tiny (electorate ~400–500 registered; several unopposed),
  so some retrieved filings may themselves be small-budget certificates, and the 2023 (unopposed
  A/B/C) and 2025 (unopposed Mayor + Seat D) candidates may be threshold-exempt with little or
  nothing to file even where a portal were reachable. Recorded as a caveat, not asserted
  per-candidate.

## Double-count / dedup (SKILL §6 — the trap)

`is_incremental` is left **BLANK** on every row — classifying cumulative-vs-incremental requires
the deferred extraction pass. Utah convention: the **December year-end summary**
(`filing_type=summary`, 6 rows: Bailey 2019, Stitzer 2019, Clayton 2019, Olsen 2021, Severson 2021,
R. Patrick 2021) is the cumulative cycle total; the October/November interims are period reports.
**Do NOT sum a candidate's filings.** Any per-candidate / per-cycle dollar total MUST go through
`scripts/campaign_finance/cycle_totals.py`, never a raw row sum. The 6 COI rows carry no dollars at all.

## Year attribution — OCR-verified, not guessed (build note)

The county static page shows only a **month** per link, not a year. The 5 founding files are
fixed to 2016 by the `/2016_disclosures/november/` path AND their "2016 Financial Disclosure
Report" header. The 14 root-level files carry no year in the URL; each file's year was read from
its printed **"&lt;YYYY&gt; Financial Disclosure Report"** title line via `tesseract` OCR of page 1
(`date_precision = county_month_label_year_ocr`) — this is what surfaced the 2019 cohort (flag #2).
The 6 town COI files carry `date_precision = city_page_label`.

## Formats

- **Scanned (`format=scanned`, 20 rows):** all 19 SLCo county PDFs + the 2026 Kathleen Bailey COI
  (image scan). `pdftotext -layout` yields ~0 characters.
- **Text/born-digital (`format=text`, 5 rows):** the 2025 candidate COI packet + the 2026 Clayton /
  Stitzer / McCalmon / Pratt COIs. `extraction_method = "none (raw acquisition; text/OCR/vision
  deferred)"` on **every** row regardless — this layer computes no dollar totals.

## Honest gaps / non-issues

- **2016 is the founding township cycle** — below the repo's 2017 data floor, but the founders
  overlap the later roster (Patrick, Stitzer, Bailey, Baxter, Clayton), so the 5 founding filings
  are retained as valid context (clearly labeled `election_year=2016`).
- **2023 (metro township):** blocked by the EasyVote SPA HTTP-500/auth-gate — `unrecovered.csv`
  (3 seats; unopposed → possibly Small-Budget-exempt).
- **2025 campaign finance:** none posted — both certified candidates unopposed/threshold-exempt;
  `unrecovered.csv` (2 offices). Only Conflict-of-Interest forms exist for the town era.
- **COI vs campaign finance:** the 6 `coi_disclosure` rows are conflict-of-interest statements
  (10-3-1301 / HB80-2024), retained per the SKILL's COI→coi_disclosure note; they are **not**
  contribution/expenditure reports and carry no dollar figures.

## 2026-07-17 — STRUCTURED DOLLAR LAYER BUILT (addendum)

`build_finance.py` (family `vision_cache`) consumes the 19 `vision/*.json` caches into the derived
CSVs. `validate_finance.py` PASS (0 fails; 6 WARNs = the 6 COI rows are OUT OF SCOPE and correctly
have no filing_totals row). `scripts/validate_city.py copperton_city_council/` unchanged (0 FAIL).

**Row counts:** filing_totals 19 · contributions 10 · expenditures 15 · cycle_totals 14
candidate-cycles. **11/19 filings reconcile both sides; 8 are honest totals-only/blank** (fee-only
$50 pages or $0 summaries that print a cover total over an itemized-nothing schedule — reconcile
UNKNOWN, never a fabricated mismatch). Confirmed tiny-town shape: substantive itemization only in
Ron Patrick 2016 ($381.97) and Kathleen Bailey 2019 Oct ($428.40); everything else is filing-fee or
zero. No in-kind rows anywhere.

**Dollar reality (now computed, was a caveat above):** the largest cycle totals are Kathleen Bailey
2019 ($450 raised / $500 spent — see the override note) and Ron Patrick 2016 ($381.97/$381.97). All
other candidate-cycles are ≤ $250. Small-Budget territory throughout, as predicted.

**cycle_overrides.csv (1 row) — Kathleen Bailey 2019:** her Dec "summary"-typed filing is itself a
disjoint period report ($71.60 loan-repayment-to-self, disjoint from the Oct interim's $428.40), so
the generic summary-vs-interim max() rule dropped the Dec $71.60. Override = sum of both filings
(raised $450 / spent $500). Documented, evidence-cited; carried as the cycle_totals review_flag.

**donor_aliases.csv (3 rows, evidence-cited):** "Sean Clayton (self)" + "Tessa Stitzer (filing fee)"
→ candidate-self (parentheticals defeated the deterministic matcher → unknown); "Reagan Outdoor
Advertising" → business (Utah billboard company; read as person-shaped → individual). Raw-PDF
spot-check (Ron Patrick 2016) verified every itemized amount + name + the $381.97/$381.97 cover.

**Verbatim quirks preserved (never corrected):** Baxter-2016 struck-through ending balance = null;
Severson-2021 Dec blank this-period totals = null; Column-B YTD figures deliberately not captured in
the caches (per-period Column A only).

**Follow-up (report-only, not started here):** the 2025-10-15 OCR-upgrade lead noted in the
pmn_backfill layer is a SEPARATE minutes task, unrelated to this CF build. The 2023 EasyVote gap and
2025 unopposed/threshold-exempt honest-zeros are unchanged.
