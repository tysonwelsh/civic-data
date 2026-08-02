# RECON — Wasatch County county-office campaign finance

**Recon + acquisition date: 2026-08-01.** Scope: **COUNTY offices only** (County Council /
pre-2016 Commission, Clerk/Auditor, Sheriff, Attorney, Assessor, Recorder, Treasurer, Surveyor).
School-board filings are out of scope by instruction and are recorded, not fetched
(`out_of_scope.csv`).

This file records **what was probed and what each channel actually held** — including the dead
ends, because a documented negative is the only thing that makes a later "we already looked"
trustworthy. The candidate→filing→office mapping and the gap ledger live in `AVAILABILITY.md`;
how to *use* the data is in `CLAUDE.md`.

---

## 1. The finding that shapes everything: THREE CMS eras, and the middle one is still alive

Wasatch County has moved web platforms twice, and **each era hosts its own campaign-finance
filings at its own URL shape**. Critically, the *middle* platform was never taken down:

| era | host / path shape | status 2026-08-01 | cycles it holds |
|---|---|---|---|
| **DNN ("Portals")** | `wasatch.utah.gov/Portals/0/Clerk/Pdfs/Elections/<cycle>/…` | **STILL LIVE — serves PDFs 200** (the *pages* 301 away, the *files* do not) | 2018, 2020, 2022, 2024-June |
| **Jadu** | `www.wasatchcounty.gov/downloads/file/<id>/<slug>` | **DEAD — every id 404s** | 2024 general (only) |
| **CivicPlus** | `www.wasatchcounty.gov/DocumentCenter/View/<id>/<slug>` | live | 2026 |

**Consequence: 104 of 111 filings were pulled from the government's own origin host**, not from
an archive — a much stronger provenance position than the "portal decayed, go to Wayback"
pattern that dominates the city repos. Only the **2024 general** reports depend on the Internet
Archive, because they existed *only* on the Jadu host, which is gone.

The live CivicPlus elections hub (`wasatchcounty.gov/elections`) shows **the 2026 cycle and
nothing else** — there is no archive page, no year picker, no browsable DocumentCenter tree.
Every pre-2026 cycle had to be recovered by finding the *listing page of its own era* in the
Wayback Machine and reading the anchors off it. Those listing pages are retained verbatim in
`raw/index_pages/` (they are the provenance of the candidate→office→filing map, which the PDFs
themselves often cannot supply because the office field is handwritten).

---

## 2. Channels probed, and what each held

| # | channel / URL probed | result |
|---|---|---|
| 1 | `wasatchcounty.gov/elections` (live CivicPlus) | ✅ **2026 only** — 15 March + 16 June disclosure links (13 county + 3 school board in June). Anchors the 2026 cycle. |
| 2 | `wasatchcounty.gov/DocumentCenter`, `/DocumentCenter/Index/1`, `/DocumentCenter/Home/Index` | ❌ no browsable folder tree exposed; documents reachable by `View/<id>` only. No older cycles found this way. |
| 3 | `wasatchcounty.gov/downloads/file/*` (Jadu) — live | ❌ **404 on every id** (CMS retired). |
| 4 | Wayback capture of the Jadu elections page, `20241214193750` | ✅ **the 2024 cycle's whole candidate list with office headings**, each candidate carrying a Declaration-of-Candidacy link + 1–3 "Disclosure Notice" links. This single capture is the only surviving 2024 index. |
| 5 | `wasatch.utah.gov/Portals/0/Clerk/Pdfs/Elections/*` (DNN) — live origin | ✅ **2018 `2018Elections/DC/`, 2020 `2020 Election/Financial/`, 2022 `2022 Election/Financial/`, 2024 `2024 Election/DisclosureNotices/`** all fetch 200 from the origin today. |
| 6 | Wayback `wasatch.utah.gov/Clerk` captures (2016, 2018-09, 2019-07, 2020-12, 2022-10, 2022-12) | ✅ the DNN-era listing pages: office headings + per-candidate filing links. **2022-10 vs 2022-12 differ** — the December capture *replaced* the June/primary links with general links, so BOTH captures were needed to recover the full 2022 set (13 filings, not 6). |
| 7 | Wayback `wasatch.utah.gov/Clerk` capture **2016-10** | ❌ **no campaign-finance links of any kind.** Combined with (8), this is the evidence that county-published CF starts at **2018**. |
| 8 | Wayback CDX over `wasatch.utah.gov/Portals/0/Clerk/Pdfs/Elections/*` (258 urls, folder census) | ✅ folders exist for 2016, 2018Elections, 2020 Election(+Financial, 55 files), 2021, 2022 Election(+Voting Precincts), 2022 Redistricting, 2023, 2024 Election(+Candidates/DisclosureNotices/PresPrimary/RepublicanPrimary). ❌ **no `Financial` folder under 2016** and no 2014 folder at all. |
| 9 | `disclosures.utah.gov/Municipal/wasatch` (Lt. Governor) — **recursive sweep, every subfolder** | ⚠️ mixed — see §3. Yielded **2010 (4 county filings)** and **2024 (1)**; **2012 is an honest county ZERO**; all odd-year folders are municipal. |
| 10 | `disclosures.utah.gov/Municipal/wasatch_2014 / _2016 / _2018 / _2020 / _2022` | ❌ **`does not exist`** (2014/2016/2018/2022) or a bare link back to the county clerk page (2020). The state system does not mirror Wasatch's county-office filings. |
| 11 | Old host `co.wasatch.ut.us` (pre-2014) CDX | ❌ election *pages* captured (2004 candidate list, 2012 voting districts) but **no campaign-finance PDFs**. |
| 12 | Wayback availability API, per-id, for the 5 missing 2024 general reports | ❌ `archived_snapshots: {}` — genuinely never captured. See §5. |

---

## 3. The state-site sweep was done under the FORM-HEADER rule

Per the coordinator's Juab finding, the Lt. Governor's `/Municipal/<county>_<year>` folders
sub-file by the **candidate's town of residence**, so a county-office filing can hide inside a
town-labelled folder and a folder label can never clear a folder. This sweep therefore
**walked every `wasatch_*` subfolder recursively** (36 folders, 156 files enumerated) and
classified by the **form header printed inside the PDF**, not by the folder name:

- **county filing** → `FINANCIAL CAMPAIGN REPORT` / *"the financial campaign law is in the Utah
  Code reference **17-16-6.5**"* / addressed *"TO ______ County Clerk"*.
- **school-board filing** → the same sheet overprinted `SCHOOL BOARD CANDIDATE` and citing
  **20A-11-1301**.
- Many are image-only; where `pdftotext` could not settle it, **the page was rendered and read**
  (2010 James Koson, 2018 Tyler Wilson Bluth).

What that discipline actually changed:

- **`wasatch_2012 Primary` looks like a 6-filing county haul and is not.** All six
  (Baird, Kelson, Jacobsmeyer, Davis, Sorenson, Cowley) carry the **SCHOOL BOARD CANDIDATE**
  header. **2012 county-office filings on the state site: ZERO.** Taking the folder label at
  face value would have booked six phantom county rows.
- **`wasatch_2010 Primary` is genuinely mixed** — 4 county (Yergensen, Koson, McDonald, Sweat)
  + 6 school board (Horner ×2, Jones ×2, Heywood ×2). Koson's office field is handwritten and
  OCR-illegible; the rendered page reads **"Wasatch County Attorney", district "County wide"**.
- No **even-year town subfolder** exists for Wasatch (unlike Juab's `juab_2014_Mona`), so the
  residence-town trap did not extend depth here — but the check was run, and that negative is
  the point.
- The odd-year folders (2009/2011/2013/2017/2019/2021/2023/2025) are municipal-cycle filings for
  Heber City, Midway, Charleston, Hideout, Daniel and Wallsburg. Utah county offices are elected
  in **even** years, so none can hold a county-office C&E report; they are listed here as
  probed-and-excluded rather than silently skipped.

`disclosures.utah.gov` also proves it *knows* it is not the system of record: the
`wasatch_2020` folder contains no filings at all — just a link back to
`Https---Www.Wasatch.Utah.Gov-Clerk#57712-Elections---Voting`.

---

## 4. Portal labels vs. file contents — what verification caught

Every claim below came from opening the file, not from the link text.

- **The form family changes mid-2024, not at the CMS boundary.** 65 filings use the older Utah
  county **`FINANCIAL CAMPAIGN REPORT` + Form A/B** sheet; 44 use Wasatch's newer
  **`CAMPAIGN FINANCIAL DISCLOSURE` + Table A/B**. The **2024 cycle is mixed** — 4 filings on the
  old form, 16 on the new — so form family is a **per-filing** property and is stored per row
  (`index.csv.form_family`), never inferred from the year.
  > ⚠ **CORRECTED 2026-08-01 — this paragraph is the OCR-header reading and it is wrong.** All
  > 111 covers were then read by vision, and the split is clean and cycle-aligned: **2010 + 2022
  > Carr four-line (17) · 2018 + 2020 Wasatch three-line (45) · 2024 + 2026 Table A/B (49)**.
  > **The 2024 cycle is NOT mixed** — all 21 of its filings are on the new sheet. The header
  > classifier is fooled because **the 2024 vintage of the NEW sheet still cites Utah Code
  > 17-16-6.5** (17-70-4 only from 2026). `index.csv.form_family` is consequently wrong on 6 rows
  > (enumerated in `AVAILABILITY.md` → "Stated-totals coverage"). The paragraph above is left in
  > place because it records what the acquisition pass could see; use
  > `filing_totals.filing_regime` or `vision/<key>.json._meta.form_variant_vision` instead.
- **The two families disagree about what a report means.** The old sheet is **cumulative** — a
  three-column `TOTALS FROM LAST REPORT + TOTALS FOR THIS REPORT = CUMULATIVE REPORT` box
  (verified on Granger 2022-11-01: $0 / $0 / $450 expenses / −$450 balance). The new sheet is
  **period-scoped** — Bonner's 2024 general report states *"Covering Sep 26 to Oct 24, 2024"*
  with its own $700 / $3,612.69 totals. **A cycle total is a different computation on each.**
- **The county's own form misprints its own statute.** The 2018/2020 Wasatch sheet cites
  *"Utah Code reference **17-15-6.5**"*; the correct citation (and the one the 2010/2022 Carr
  Printing sheet uses) is **17-16-6.5**. Retained verbatim — a source typo is data.
- **A filing can contradict its own portal label.** `S. Farrell Elimination Report` (2026-06)
  is Steve Farrell's, but the form has **both** the *Partisan Convention Report* and the
  *Candidate Withdrawal/Disqualification/Elimination Report* boxes checked. Recorded as
  published, flagged in `index.csv.notes`, not silently resolved.
- **A declaration is not a disclosure.** On the 2024 Jadu page each candidate carries a
  Declaration-of-Candidacy link *and* "Disclosure Notice" links under the same heading; only the
  latter are campaign-finance reports. On the 2026 page, **Paul Moore** (unaffiliated, Sheriff)
  filed a declaration and **has no CF filing published at all** — an honest absence, not a fetch
  failure.

---

## 5. What could not be recovered (the whole gap ledger)

- **5 of the 12 2024 general reports** — Crittenden, Broughton, Nelson, Gibbs, and Adams'
  9-30-24 report. Their Jadu ids (733/737/738/725/724) **404 at origin** *and* return
  `archived_snapshots: {}` from the Wayback availability API. Dead on every channel; recorded in
  `unrecovered.csv`. **No candidate is entirely absent** — each has a June filing, and Adams has
  his 10-29-24 report.
- **2014 and 2016** — no CF filings published on any channel. The 2016-10 DNN clerk page carries
  none, the DNN `Elections/` tree has no 2014 folder and no 2016 `Financial` folder, and the
  state site has no `wasatch_2014` / `wasatch_2016` folder. **Publication appears to begin in
  2018**; this is a publication gap, not a retrieval gap.
- **Pre-2010** — the state site's `wasatch_2008` folder is empty and its `2008_School Board`
  subfolder is school board only. The `co.wasatch.ut.us` era published no CF PDFs.
- **2012** — county-office ZERO, per §3.

## 6. Reproducing this

```
python3 refetch.py            # verify all 111 retained PDFs against index.csv sha256 (currently 111/111)
python3 refetch.py --repair   # re-download anything missing, from source_url or archive_url
python3 extract_text.py       # rebuild text/ sidecars + text_extraction.csv
python3 build_index.py        # rebuild index.csv / out_of_scope.csv / unrecovered.csv
```

Two operational notes that cost time here and will cost it again: **CivicPlus 403s a bare
fetcher** (an archive-browser User-Agent fixes it — GOTCHAS.md), and the **Wayback CDX API rate-
limits hard** into 503s and outright connection refusals under a sweep, so per-URL availability
checks with backoff beat one big CDX query when you need a definitive negative.
