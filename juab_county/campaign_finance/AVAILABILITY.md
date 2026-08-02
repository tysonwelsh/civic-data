# Juab County campaign finance — availability, coverage & honest gaps

**As-of 2026-08-02.** Scope: **Juab COUNTY-office** candidates — Commission (Seats A/B/C),
Clerk/Auditor, Sheriff, Attorney, Assessor, Recorder/Surveyor, Treasurer. Per-channel evidence is
in `RECON.md`; every acquired file's provenance is in `index.csv`.

**BORN-DIGITAL SCOPE: ZERO — determined 2026-08-02 (TRANCHE 3 Phase A).** `pdftotext -layout`
over **all 82 retained raws** returns **0 non-whitespace characters in total**: every file is an
image scan, so no text-layer form family applies and the sweep that wired six new county
families elsewhere correctly built **nothing** here. The existing hand-verified **2020-only**
itemized layer (`contributions.csv` 4 rows / `expenditures.csv` 23 rows, from
`vision/transcripts.json`) was **not touched**. Itemizing 2010/2014 remains Phase B (vision)
work — an empty itemized layer there means *not transcribed*, never *no donors*.

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
   any **interim** 2010/2014 reports.

## Privacy

`PRIVACY.md` applies. These are **campaign-finance filings** — the repo's standing rule is that
campaign_finance text is **never redacted**; contributor names and the addresses printed on Form A
are the disclosure. The `raw/` scans are retained unaltered. Candidates' own home addresses and
phone numbers appear on the form face and are transcribed only as `residence_city` in the derived
CSVs — the street address and phone lines are deliberately **not** carried into the derived layer.

## Itemized transcription queue (scoped, honest gap)

`filing_totals.csv` carries the page-1 stated totals for **all 27** filings. The itemized Form A
(contributions) / Form B (expenditures) pages are transcribed for the **3 filings of 2020 only**
(`itemized_transcribed=1`; 4 contribution rows, 23 expenditure rows). The 24 filings of 2010 and
2014 carry `itemized_transcribed=0` and blank `reconciles_*` — a **stated-totals-only** state, per
SCHEMA.md's "Totals-only filings reconcile as unknown, never a fabricated mismatch."

Remaining work is bounded and enumerated: 18 of the 24 have a non-zero stated total and therefore
a populated Form A/B (the other 6 are all-zero filings whose itemized pages are blank by
construction). That is **≈36 page images** to transcribe by the `cf-vision-transcribe` method into
`vision/transcripts.json`, after which `build_finance.py` regenerates the derived CSVs unchanged.

## Reconciliation state of what IS transcribed

| filing | contributions | expenditures | outcome |
|---|---|---|---|
| Neil Vance Cook (2020, Commission) | none itemized, stated 0 | 5 rows = **2081.03** vs stated **2081.03** | **reconciles exactly** |
| Debra Prisbrey Zirbes (2020, Recorder/Surveyor) | 2 rows = 70.00; stated 20.00 named + 50.00 anon-surrendered | 8 rows = 2646.26; **stated total is BLANK on the form** | does not reconcile — internal inconsistency retained as filed |
| Marvin Garr Kenison (2020, Commission) | 2 rows; page-1 contribution line blank | 10 rows, **2 amounts unreadable (left blank, not guessed)** | cannot reconcile — flagged `needs_review` |

Three additional filings carry **filer errors retained verbatim** rather than corrected:
Douglas Scott Anderson (2014) and Robert Garrett (2014) entered every figure in the "totals from
last report" column, leaving cumulative blank (kept in `stated_prior`, never promoted); Robert
McKell Williams (2014) wrote prose amounts "$150.00 + SIGNS" / "$1010.00 + SIGNS" (numeric fields
blank, verbatim string preserved). LuWayne Walker's (2010) cumulative >$50 cell is overwritten and
unreadable — left blank rather than resolved to 125.00 or 1125.00.
