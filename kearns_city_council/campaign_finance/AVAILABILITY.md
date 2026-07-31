# Kearns — Campaign-Finance Disclosures: Availability

> **2026-07-18 — STRUCTURED DOLLAR LAYER BUILT.** The vision caches are now consumed by
> `build_finance.py` (family `vision_cache`) into `contributions.csv` (61) /
> `expenditures.csv` (80) / `filing_totals.csv` (38) / `cycle_totals.csv` (24). Coverage of
> the STRUCTURED layer is **2016–2021 only** — exactly the retrievable set below. The **2023
> and 2025 cycles remain honest acquisition gaps** (EasyVote auth-wall / city-site Cloudflare)
> with NO filing_totals rows; per-candidate/per-cycle dollar totals live in `cycle_totals.csv`
> (never sum `filing_totals`). 25/38 filings reconcile both sides; 12 are totals-only UNKNOWN
> (≤$500 Summary-only forms + Higginson's blank 2019 dissolution summary); 1 verbatim mismatch
> (Richards 2019 interim expenditures +5.23). One documented `cycle_overrides.csv` row
> (Butterfield 2019 → 296.90/296.90, from the Dec form's own Column-B YTD). See
> `campaign_finance/CLAUDE.md` for the full build record.

**As-of:** 2026-07-13 (vision transcription added 2026-07-17; structured layer 2026-07-18) ·
**Layer:** structured dollar layer built 2026-07-18 (was ACQUISITION-ONLY); raw filings
retained; `index.csv` unchanged. **Vision cache (2026-07-17):** all 38 scanned filings transcribed to
`vision/<hash>.json` via the Read tool ($0 API) — verbatim contribution/expenditure rows +
printed summary totals, illegible→null, never inferred. Transcription artifact only; see
`CLAUDE.md` § `vision/`. **Cycles in scope:** township
2016(founding)/2017/2019/2021/2023 + the 2025 first city-era election.

Kearns (~36k pop., Salt Lake County) is a **metro township (2017–2025) → city (2024-05;
first city election 2025-11-04)**. Its elections are administered by the **Salt Lake County
Clerk**. Because the filing jurisdiction differs by era, the finance record splits cleanly:

| Cycle | Era | Filing host | Retrieved? |
|---|---|---|---|
| 2016 (founding) | metro township | SLCo Clerk **static** disclosures page | **YES — 16 PDFs** |
| 2017 | metro township | SLCo Clerk static page | **YES — 2 PDFs** |
| 2019 | metro township | SLCo Clerk static page | **YES — 14 PDFs** |
| 2021 | metro township | SLCo Clerk static page | **YES — 6 PDFs** |
| **2023** | metro township | SLCo **EasyVote** portal (2022+) | **NO — portal reCAPTCHA/auth-gated** |
| **2025** | **city** | **kearns.utah.gov** (city site) | **NO — Cloudflare-blocked** |

**38 township campaign-finance filings retrieved** (all 2016–2021), all from the Salt Lake
County Clerk's static financial-disclosures archive. These are **candidate campaign-finance
(contribution/expenditure) reports** — the county's "Financial Disclosure Report For a
Candidate" — **not** conflict-of-interest forms. Every one is a **scanned/redacted image
PDF** (`format=scanned`); dollar extraction is deferred. **2023 and 2025 yielded no files**
— both are honest, well-explained access gaps (see below and `unrecovered.csv`).

## What was checked (search order — SKILL §6, cluster order for a metro-township entity)

1. **SLCo Clerk financial-disclosures — the PRIMARY yield.**
   - `saltlakecounty.gov/clerk/elections/financial-disclosures/metro-township-councils/` —
     a **static page** listing per-candidate PDF links grouped under "Kearns Metro Township
     Council 1–5". It holds **2016–2021 only** (the county moved 2022+ filing to EasyVote).
     Harvested **38 Kearns-attributed PDFs** (`/globalassets/…/financial_disclosure/…pdf`;
     anchors read directly, never guessed). This is where the entire retrievable Kearns
     finance record lives.
   - `saltlakecounty.gov/clerk/elections/financial-disclosures/` states the filing rule that
     confirms the jurisdiction split: **"county office, metro township and school board
     candidates"** file with the county — a **city** files with its own recorder.
2. **SLCo EasyVote portal (2022+)** — `saltlakecountyut.easyvotecampaignfinance.com`
   (Angular SPA) → API `ecf-api.easyvoteapp.com`. The public-filings list requires an
   anonymous website-user token from `/authentication/getwebsiteuser/saltlakecountyut`,
   which **returns HTTP 500** to a polite GET (the page also gates on Google reCAPTCHA v3).
   The document-search endpoints (`/filer/documentsearch/{CustomerId}`,
   `/filer/racedocumentsearch/{…}`) all need that token + an `Easy-Vote-Authenticated-User`
   header. **Under GET-only, no-POST, no-reCAPTCHA-bypass rules this portal is unreachable**,
   so **2023 township filings (Schaeffer/Valdez D1, Butterfield/Geertsen D3, Bush D5) could
   not be retrieved.** This is the same "2022 and later" boundary the static page documents.
3. **Kearns city site (2025 filings)** — `kearns.utah.gov`. **Cloudflare JS-challenge blocks
   every request** (browser UA included); the `/media/<id>` PDF endpoints return **HTTP 403**.
   The 2025 city-era candidates file here (city recorder Diana Baun, MSD staff), NOT with the
   county. **→ the Cloudflare block prevented all city-hosted 2025 access** (see the FLAG).
4. **Wayback Machine** (`web.archive.org` CDX, via `polite_fetch.py`).
   - Recovered exactly **one** useful 2025 artifact: the archived landing page
     `kearns.utah.gov/township/page/campaign-finance-disclosure-lyndsay-longtin`
     (captured 2025-11-04, HTTP **200**). Its "Supporting Documents" block **proves Longtin
     filed two reports** — a "Primary Campaign Finance Disclosure" (2.21 MB, `/media/3531`)
     and an "Oct. 7 General Election Campaign Finance Disclosure" (2.17 MB, `/media/3756`).
     **But Wayback did NOT archive the /media PDFs** (its Kearns media captures stop at id
     **3241**, mid-2024; Longtin's are 3531/3756) and no OTHER 2025 candidate page was
     captured. The landing HTML is retained at `raw/2025_longtin_cf_landing_wayback.html` as
     evidence-of-existence (it is NOT a filing, so it is not an `index.csv` row).
   - Wayback's `saltlakecounty.gov/globalassets*` captures for "kearns" are only the same
     2016–2021 disclosure PDFs (older `/niftic/` path) — no 2023/2025.
5. **State `disclosures.utah.gov/Municipal` (long-shot; the metro-township cluster lesson).**
   - **2023 Salt Lake folder: NO Kearns entry at all** — the metro-township-origin entities
     (Kearns / White City / Magna / Copperton / Emigration) are absent from the state tree,
     exactly as the White City build found.
   - **2025 Salt Lake folder: a LINK-FARM, not a host** — it lists **"Kearns (Campaign
     Finance)" → kearns.utah.gov/community/page/2025-election** and **"Kearns" →
     kearns.utah.gov/resource-center/page/disclosure-statements**, both **Cloudflare-blocked
     city pages**. The state hosts **no** Kearns PDFs. (It also lists **"Kearns Improvement
     District" → kidwater4ut.gov** — the water-district **DECOY**, excluded.)
6. **Alternate county search** `disclosure.saltlakecounty.gov/Search/PublicSearch` — the host
   is **unreachable** (connection reset); superseded by EasyVote.

## Coverage vs the election roster (`election_results/kearns_races.csv`)

| Cycle | Contest(s) | Candidates in kearns_races.csv | Finance filings held | Status |
|---|---|---|---|---|
| 2016 (founding) | Seats 1–5 | Schaeffer/Helsten, Peterson, Perry/Geertsen(+primary field), Snow, Bush/Richards | **16** | Founding cycle captured (all seat winners + runners-up + the Seat-3 primary field) |
| 2017 | Seats 2 & 4 | Peterson, Snow (both uncontested) | **2** | Both filers captured |
| 2019 | Districts 1/3/5 | Schaeffer/Higginson, Butterfield/Brown, Bush/Richards | **14** | All six certified candidates captured (+ a Geertsen 2019 filing — see FLAG 2) |
| 2021 | Districts 2 & 4 | Peterson/Gibson, Snow | **6** | All three certified candidates captured |
| **2023** | Districts 1/3/5 | Schaeffer/Valdez, Butterfield/Geertsen, Bush | **0** | **GAP — EasyVote portal reCAPTCHA/auth-gated** |
| **2025** | Mayor + D2 + D4 | Valdez/Snow, Longtin/Hansen, Colby/Snow | **0** (Longtin's 2 confirmed to EXIST) | **GAP — city site Cloudflare-blocked** |

**2016–2021 coverage is effectively complete** for the retrievable (pre-EasyVote) era: every
certified township winner and runner-up filed and is captured, plus the 2016 Seat-3 primary
field (Lefler, Welch, Walton) who did not advance to the general. 2023 and 2025 are the two
honest gaps, each with a specific, documented technical barrier.

## Threshold-exemption / dollar reality

- **Not computed here.** All 38 filings are scanned image PDFs; contribution/expenditure
  dollars require the deferred OCR/vision pass. No dollar figure is asserted.
- **Small-Budget exemption is live for this entity.** The SLCo Clerk allows a **Small Budget
  Campaign Certificate** for campaigns under **$2,000** (then only a general + year-end report
  is required). Kearns township races are small (2021 D2 total 108 votes; several uncontested),
  so some retrieved filings may themselves be small-budget certificates, and some 2023
  candidates (esp. **uncontested Bush D5**) may be threshold-exempt with little or nothing to
  retrieve even if EasyVote were reachable. Recorded as a caveat, not asserted per-candidate.

## Double-count / dedup (SKILL §6)

`is_incremental` is left **BLANK** on every row — determining cumulative-vs-incremental
requires reading the scanned forms (the deferred pass). The Utah convention is that the
**December year-end summary** (`filing_type=summary`, 8 rows) is the cumulative cycle total
and the interims are period reports — **so do NOT sum a candidate's filings** before the
extraction pass classifies each one. Any per-candidate/per-cycle dollar total MUST go through
`scripts/campaign_finance/cycle_totals.py`, never a raw row sum.

## Discrepancy FLAGS (recorded here only — do NOT edit `election_results/`)

1. **2023 & 2025 finance gaps are technical-access gaps, not "nothing was filed."** Unlike
   White City (where the pre-2024 metro-township era genuinely published nothing anywhere),
   Kearns 2023 filings almost certainly EXIST inside EasyVote (the portal is the county's
   2022+ system) and 2025 filings **provably exist** (Longtin's landing page lists two). The
   barrier is retrieval (reCAPTCHA/auth on EasyVote; Cloudflare on the city site), not absence.
   Recoverable later via a browser/residential fetch of kearns.utah.gov, an EasyVote export,
   or a future Wayback capture of the `/media` PDFs. No election contest is contradicted.
2. **A 2019 Christopher Geertsen finance filing surfaces a candidate the certified election
   record does not list.** `christophergeertsen2019.pdf` is an August-2019 candidate
   campaign-finance filing, but the certified **2019 District 3** contest in
   `kearns_races.csv` is **Butterfield vs Ruby Brown only** — Geertsen is not a 2019 D3
   candidate of record (he ran 2016 and 2023). Most likely he **declared for 2019 then
   withdrew** (or filed but was not on the general ballot). Indexed with
   `join_confidence=low` + a note. **Flagged, not reconciled** — `election_results/` is not
   edited (per the SKILL: finance data may surface election-record edges; flag, don't fix).
3. **Water-district decoy excluded.** The state 2025 link-farm lists **Kearns Improvement
   District** (`kidwater4ut.gov`, water) — a separate special district; NOT ingested. The
   Oquirrh Park and Kearns MSD decoys did not surface in any finance source.
4. **These are campaign finance, not COI.** The 38 retrieved filings are candidate
   contribution/expenditure reports. The 2025 city site ALSO advertises a separate
   "Disclosure Statements" (conflict-of-interest, Utah Code 10-3-1301) page — but it too is
   Cloudflare-blocked, so **no `coi_disclosure` rows were retrieved** for Kearns (unlike
   White City, whose city site was reachable).

## Formats

- **Scanned (`format=scanned`, all 38):** every SLCo Clerk "_redacted" disclosure PDF is an
  image scan (`pdftotext -layout` yields 0 characters). `extraction_method = "none (raw
  acquisition; OCR/vision deferred)"` on every row. No `text/` sidecars and no dollar parsing
  in this layer. A later vision pass (`/cf-vision-transcribe`) can add dollar totals.

## Honest gaps / non-issues

- **2016 is the founding township cycle** — below the repo's 2017 minutes floor, but the
  elections layer covers 2016 and these founding filers overlap the later roster, so the 16
  founding-cycle filings are **retained as valid context** (clearly labeled `election_year=2016`).
- **2023 (metro township):** blocked by the EasyVote reCAPTCHA/auth-gate — see FLAG 1 +
  `unrecovered.csv` (5 candidates).
- **2025 (city):** blocked by Cloudflare on `kearns.utah.gov` — see FLAG 1 + `unrecovered.csv`
  (6 candidates; Longtin's 2 filings confirmed to exist via the retained Wayback landing HTML).
- **No conflict-of-interest (`coi_disclosure`) rows** — the city's COI page is Cloudflare-blocked.
