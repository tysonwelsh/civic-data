# Juab County campaign finance — availability, coverage & honest gaps

**As-of 2026-08-14.** Scope: **Juab COUNTY-office** candidates — Commission (Seats A/B/C),
Clerk/Auditor, Sheriff, Attorney, Assessor, Recorder/Surveyor, Treasurer. Per-channel evidence is
in `RECON.md`; every acquired file's provenance is in `index.csv`.

**ITEMIZATION IS COMPLETE — the county is CLOSED (2026-08-14).** Every one of the **27**
county-office filings now carries a real donor/vendor layer or a reasoned statement of why no
schedule exists: **187 itemized rows** (46 contributions + 141 expenditures) over 2010, 2014 and
2020. See "The itemization wave" below for the measured reconciliation and the gap ledger.

**BORN-DIGITAL SCOPE: ZERO — determined 2026-08-02 (TRANCHE 3 Phase A).** `pdftotext -layout`
over **all 82 retained raws** returns **0 non-whitespace characters in total**: every file is an
image scan, so no text-layer form family applies and the sweep that wired six new county
families elsewhere correctly built **nothing** here. Every figure in this module is therefore
**vision-read from the page image** — there is no parsed alternative to compare it against, which
is why the reconciliation gates below carry the weight.

**Result: PARTIAL — a real dataset for three cycles, a defensible negative for the rest.**
27 county-office filings across **2010, 2014, 2020**, covering **all seven county-office
classes**. No county-office filing is published anywhere public for **2012, 2016, 2018, 2022,
2024, 2026** — and that is a property of Utah's disclosure plumbing, not a search failure.

## Where Juab county-office filings actually live

**Not on the county website. On the Lt. Governor's `disclosures.utah.gov` system, inside the
folder tree labelled "Municipal", in the EVEN-year folders, sub-foldered by the candidate's town
of residence.** The label lies twice over — "Municipal" is the tree name for the whole
local-government upload area, and "Nephi"/"Mona"/"Levan"/"Callao" are residence towns, not
jurisdictions. The discriminator is the form header, visible only inside the PDF:

| form | statute | tier |
|---|---|---|
| **FINANCIAL CAMPAIGN REPORT**, Carr 5-5-PG | **Utah Code 17-16-6.5** (county elections) | **county office** |
| SCHOOL BOARD CANDIDATE FINANCIAL CAMPAIGN REPORT, Carr 5-4 PG School | 20A-11-1301..1305 | school board |

Every file is an **image scan** — `pdftotext` returns 0 characters on all 82 — so this is a
vision-transcription dataset, not a text-extraction one.

## Coverage

| cycle | county-office filings | offices represented | source |
|---|---|---|---|
| **2010** | 12 | Commissioner ×3, Clerk/Auditor ×2, Recorder/Surveyor ×2, Assessor ×2, Sheriff, Attorney, Treasurer | `disclosures.utah.gov/Municipal/juab_2010 primary` |
| 2012 | **0** | — | folder does not exist (probed) |
| **2014** | 12 | Commissioner ×3, Clerk/Auditor ×2, Recorder/Surveyor ×2, Sheriff ×2, Assessor, Attorney, Treasurer | `.../juab_2014_{Mona,Nephi}` |
| 2016 | **0** | — | folder does not exist (probed) |
| 2018 | **0** | — | folder does not exist (probed) |
| **2020** | 3 | Commissioner ×2, Recorder/Surveyor | `.../juab_2020_Primary` (2 multi-filing bundles) |
| 2022 | **0** | — | folder does not exist (probed) |
| 2024 | **0** | — | see "the 2024 story" below |
| 2026 | **0** | — | `juab_2026` folder exists and is **empty** |

Filing counts are per REPORT, not per candidate: 2010 carries a single (pre-general) report per
candidate; 2014 likewise; 2020 carries pre-primary reports only.

### Ceilings inside the acquired cycles

- **2010 and 2014 are single-snapshot cycles.** Only the late-October (pre-general) report was
  uploaded for county candidates; the interim reports that the school-board filers submitted in
  June and August of 2010 have no county-office counterpart in the folder. Whether interim county
  reports were filed and not uploaded, or not filed, is **unknown** — the state folder is the
  only channel and it shows one report each.
- **2020 is PRIMARY-ONLY.** The folder is named `Primary` and both bundles are June/August 2020
  filings. **No 2020 general-election county reports exist on any channel** (`juab_2020_General`
  probed, does not exist). So 2020 coverage stops at the primary.
- **Contested-race asymmetry is real, not extraction loss.** 2010 shows both a Republican and a
  Democrat for Assessor, Clerk/Auditor and Recorder/Surveyor; 2014 for Sheriff, Clerk/Auditor and
  Commissioner Seat A. Offices with one filing were, on the face of the record, uncontested or
  the opponent did not file.
- **Duplicate upload.** `Helen_Miwall_10-28-10.pdf` and `Helen_Wall_10-28-10.pdf` are the same
  document under two filenames (school-board tier; both retained, flagged in `index.csv`).
- **State filenames are unreliable.** `janice bowers 6-3-10.pdf` contains a filing signed
  *Janice J. Boswell*; `j bushwell` / `jacki bushwell` are the same person. Per GOTCHAS.md
  ("PMN/portal labels lie"), `index.csv` carries the published filename verbatim and
  `filing_totals.csv` carries the name **as written on the form**.

### The 2024 story — a documented negative with a legal cause

1. Juab County created a page, `/residents/election-information/financial-disclosures-2024/`,
   for the 2024 cycle. It publishes **a deadlines PDF and a "Submit Financial Disclosure Online
   (Coming Soon)" button** — and no filings.
2. On **2024-10-21** the Commission adopted an ordinance **establishing** campaign financial
   reporting requirements (PMN notice 948361), renumbered **Chapter 2-11 → 2-12** on 2025-02-03
   (notice 971141). Before October 2024 the county had **no local disclosure ordinance at all**;
   the only obligation was the state's 17-16-6.5, whose filings go to the County Clerk and are
   published only if the Clerk chooses to upload them to `disclosures.utah.gov`.
3. The county's own current publication is the **auth-walled SharePoint workbook** linked from
   `juabcounty.gov/disclosures/` as "Campaign Finance Reports" — HTTP 200, Microsoft sign-in
   page, not publicly readable.

So the 2016/2018/2022/2024/2026 absence is best explained as **the Clerk's office stopping the
practice of uploading county filings to the state system after 2020**, with the intended
replacement (an online submission portal + a shared workbook) not yet public. The statutory duty
under 17-16-6.5 to *file* is unchanged; what lapsed is *publication*. This is the honest reading
of the evidence, and it is a **posting-practice gap, not a data-extraction gap.** Do not fill it.

## GRAMA / clerk follow-up (recommended, not performed)

**Juab County Clerk/Auditor — Tanielle Callaway · 435-623-3410 · taniellec@juabcounty.gov ·
160 N Main, Nephi, UT 84648.** Four asks, in value order:

1. **Copies of all campaign financial statements filed under Utah Code 17-16-6.5 and County
   Ordinance Chapter 2-12 for the 2012, 2016, 2018, 2022, 2024 and 2026 county elections.**
   These are public records the Clerk holds; they were simply never uploaded.
2. **Public access to, or an export of, the "Campaign Finance Reports" workbook** linked from
   `juabcounty.gov/disclosures/` (currently a Microsoft sign-in wall).
3. **A copy of County Code Chapter 2-12 (Campaign Financial Reporting)** — the county's own PMN
   notice states a complete copy is available at the Clerk's office for public review; the
   CivicLinq code viewer is a JS-only SPA and the chapter text could not be retrieved.
4. **2020 GENERAL-election county reports** (the state folder holds primary reports only), and
   any **interim** 2010/2014 reports. The itemization wave gave this ask two specific, citable
   targets: **Clinton L Painter's earlier 2014 report**, which his October cover proves exists
   (its 1,025.57 is carried forward in his cumulative) and which the folder does not hold; and
   **the missing Form A page of Robert Garrett's 2014 filing**, whose $250.00 of stated
   contributions has no schedule in the county's 2-page scan.

## Privacy

`PRIVACY.md` applies. These are **campaign-finance filings** — the repo's standing rule is that
campaign_finance text is **never redacted**; contributor names and the addresses printed on Form A
are the disclosure. The `raw/` scans are retained unaltered. Candidates' own home addresses and
phone numbers appear on the form face and are transcribed only as `residence_city` in the derived
CSVs — the street address and phone lines are deliberately **not** carried into the derived layer.

## The itemization wave — VERIFIED 2026-08-14 (Tranche 3 Phase B, juab wave)

**The queue is CLOSED.** The 24 filings of 2010 and 2014 were vision-itemized under the wave-B2
production contract, joining the 3 filings of 2020 that the acquisition build had already
transcribed. Nothing in this module is now "not transcribed".

**Pre-flight.** The configuration (`claude-opus-5[1m]` via the Read tool; `pdftoppm -jpeg -r 200`
FULL-PAGE first read of EVERY page; escalation only as a tight cell crop at 600 dpi; the
document's own arithmetic outranking any glyph re-read) was run against the standing CF
calibration suite and scored **13 / 13 PASS**, all five negative controls held — recorded at
`_audits/cf-calibration-suite/runs.md` (2026-08-14 entry) before any bulk transcription.

### What was produced

| | |
|---|---|
| filings itemized this wave | **24** (12 × 2010, 12 × 2014) |
| filings itemized in total | **27 of 27** — the whole county-office corpus |
| rows added this wave | **160** (42 contributions + 118 expenditures) |
| rows in the module | **187** (46 contributions + 141 expenditures) |
| money itemized this wave | **$8,279.74** contributions · **$29,361.18** expenditures |
| pages read | **73** full pages (every page of every filing, incl. the printed statute page 4) |
| escalations used | **2** (both on Rick Carlton 2010 — 600 dpi tight crops of the two amount columns) |

Every row carries `pct:x,y,w,h@p<page>` **geometry** (SCHEMA.md §2a) in the trailing column of
`contributions.csv` / `expenditures.csv`, computed from the form's own printed grid: a family
PITCH per scan variant, with a **per-page ORIGIN** (these scans carry up to a third of a row of
vertical shift, and one page a full 3.5%, so a single family origin points at the wrong line).
**Verified by 600 dpi render-back on ten boxes** across both variants and both schedules, and
again end-to-end through `scripts/campaign_finance/make_snippet.py` — each box reproduced exactly
the row transcribed at that index. The two render-backs that MISSED are the reason two filings'
row indices were corrected at the source: Cody Anderson's Form A row 1 is a **struck, nameless
date fragment** (his three rows are printed rows 2–4), and Rick Carlton's 2014 Form A entries sit
on printed rows 2 and 5 (the Zions name wraps a line). Geometry is a provenance pointer, never a
value — but it is checkable, and checking it caught two real indexing errors.

### Reconciliation — per SIDE (48 sides across 24 filings)

| state | contributions | expenditures |
|---|---|---|
| **exact** against a figure the form itself prints | **18** | **16** |
| **delta**, cause named on the page | 1 | 2 |
| **unknown** — the form states no figure, or no schedule page exists | 5 | 6 |

**34 of 48 sides reconcile EXACTLY.** Not one side was withheld, and not one figure was nudged.
The gate is per side and is named per filing in `filing_totals.notes` and in the filing's
`vision/<sha256>.json` (`_meta.itemized.reconciliation`).

**The 3 deltas, each traced to the filing itself:**

| filing | side | stated | itemized | delta | cause on the page |
|---|---|---|---|---|---|
| Rick Lee Carlton (2010, Commission) | both | 2,279.15 | 2,279.25 | +0.10 | The filing is DOUBLE-ENTERED — all 13 items appear on Form A (as self-reimbursements) and again on Form B — and the filer's own two copies disagree on two cells (row 1 cents `81`/`89`, row 10 dollars `158`/`159`). No legible combination closes on 2,279.15. 600 dpi crops resolved legibility, not truth. |
| Alaina E. Lofgran (2014, Clerk/Auditor) | expenditures | 1,800.00 | 1,850.00 | +50.00 | The filer's line-3 total omits the $50.00 10/15/14 Mangelson item — and his stated ENDING BALANCE (1,850.00) is exactly the Form B sum. |
| Clinton L Painter (2014, Commission) | expenditures | 2,673.08 (cumulative) | 1,647.51 | −1,025.57 | Not a misread: Form B itemizes THIS report's period, and it reconciles **exactly** to the "totals for this report" column (1,647.51). The cumulative includes 1,025.57 from an earlier 2014 report the state folder does not hold. |

### The gap ledger — 9 sides with NO schedule page (honest non-existence, never a zero)

| filings | sides | dollars unaccounted |
|---|---|---|
| DeEtte Worthington 2010, Jared W. Eldridge 2010 (2-page scans: cover + Form A) | 2 expenditure sides | **$0** — both state 0 expenses |
| DeEtte Worthington 2014, Jared W. Eldridge 2014, Shirl Julian Nichols 2014 (1-page scans: cover only) | 6 sides | **$0** — all state 0 on every line |
| **Robert Garrett 2014 (Commission Seat A)** — the county's 2-page scan holds the cover and Form B; the Form A page does not exist in the document | 1 contribution side | **$250.00** (100.00 over-$50 + 150.00 aggregate under-$50) |

**$250.00 is the whole of the money this county states but cannot itemize** from a missing
schedule page, plus the **$1,025.57** of Painter's cumulative that belongs to a prior report the
state never uploaded. Everything else is either itemized or genuinely zero.

**7 contribution sides are REAL ZEROS** — the Form A page exists, the transcriber read it, and it
is blank (Orme, Winn, Price, Eldridge 2010, Worthington 2010, Lofgran, Painter). A real zero and a
missing page are different facts and are stored differently (`sides.<side>` =
`"transcribed"` with no rows, vs `"none"`).

### What the itemization settled that the totals tranche could not

1. **LuWayne Walker's (2010) unreadable cumulative is RESOLVED to 125.00** — by the document's own
   arithmetic, not a re-read. Line 1 reads LAST `-0-` + THIS 125.00 = CUMULATIVE, and Form A
   itemizes exactly one contribution, $125.00 from the Juab County Democratic Party. Two
   independent proofs; under 1,125.00 neither closes. The correction is recorded in
   `vision/transcripts.json` with its evidence (GOTCHAS: arithmetic closure outranks glyph
   reading — the Rhodes reversal).
2. **Walker's line 3 (expenses) is blank in all three columns, yet Form B itemizes six rows summing
   to exactly 1,420.00 — the figure he wrote on LINE 2** (aggregate contributions of $50 or less).
   The likeliest reading is a line-placement error. Both figures stand as filed; nothing was moved.
3. **Robert McKell Williams's (2014) prose totals are now fully explained.** "$150.00 + SIGNS" =
   two cash gifts ($50 + $100) plus two **in-kind** SIGNS contributions with no dollar figure;
   "$1010.00 + SIGNS" = eight Form B amounts summing to exactly 1,010.00, which is also the column
   total he wrote at the foot of the schedule.
4. **Douglas Scott Anderson's and Robert Garrett's column-placement error is now CORROBORATED, not
   just recorded**: both entered every figure in the "totals from last report" column, and their
   schedules reconcile exactly against those figures (Anderson 400.00 / 6,322.30; Garrett
   1,550.00). Anderson's over-$50 vs under-$50 split even matches his rows exactly (100+200 = 300,
   50+50 = 100). The derived `stated_*` columns stay blank, as the totals tranche left them.
5. **Michael Price's struck-through 594.50** is exactly the sum of his first six Form B rows — he
   totalled six, then added four more and restated 748.50. Both figures are explained.
6. **Craig Sperry's (2010) struck Form A row** ($20.00, no name) is why his Form A sums to 225.00
   against a stated total of 245.00: he moved that $20 to line 2 as an under-$50 aggregate. It is
   recorded as a struck entry and NOT emitted as a row.

### A reconciliation basis you must respect before quoting `reconciles_contrib`

The 17-16-6.5 form splits contributions across **line 1 (donors who gave more than $50 — itemized
on Form A)** and **line 2 (the aggregate of gifts of $50 or less — deliberately NOT itemized)**.
`filing_totals.stated_total_contributions` is the SUM of both lines, so a filing whose Form A
reconciles perfectly against line 1 can still show `reconciles_contrib=False` with a delta equal to
its line-2 aggregate. That happens on **Craig Sperry 2010 (−20.00), Alaina Lofgran 2014 (−50.00),
Craig Sperry 2014 (−139.00)** and, for the separate reason above, **LuWayne Walker 2010
(−1,420.00)**. Those four are **basis differences, not extraction defects** — each row's `notes`
says so, and the filing's cache records the true per-side verdict. Filers differ: Cody Anderson and
Kathleen Kenison itemized their small gifts on Form A anyway, so for them both bases close.

### Row-level quality (measured over the 160 rows added)

* per-row confidence **high 141 · medium 13 · low 6** (the 6 low are Rick Carlton's bistable pairs)
* **3 amounts blank for illegibility or non-existence**, never guessed (Williams's filing-fee line,
  and the two in-kind SIGNS rows which carry no dollar figure at all)
* **61 rows carry `needs_review=1`**, overwhelmingly because the form prints a date with **no year**
  (or only a month) — a year is never filled in from the report date
* **2 in-kind rows** (`in_kind=True`, amount blank) — Williams's two SIGNS donors
* dates are kept **verbatim as printed**, including `10/7 10/14` (two dates in one cell) and
  `3-14` (month/year); one Anderson date is left blank because its day digit is overwritten
