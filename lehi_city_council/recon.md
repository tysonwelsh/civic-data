# Lehi City (Utah County) — Civic Data Recon

**Date:** 2026-06-26 · **Scope:** data 2020–present · **Repo:** `/Users/tysonwelsh/civic-data/lehi_city_council/`
**Role:** mapping only (no bulk download / dataset build).

City: Lehi, Utah · Utah County · UGRC CountyID **25** · pop. ~90k, fast-growing "Silicon Slopes".
City Recorder: Teisha Wilson — 385-201-2269 · twilson@lehi-ut.gov.

---

## 1. Council meeting minutes

**Portal vendor: Granicus** (ViewPublisher / MediaPlayer / MinutesViewer). Host: `lehi.granicus.com`.
- Meeting calendar (all bodies, single view): `https://lehi.granicus.com/ViewPublisher.php?view_id=1`
- City landing page: `https://www.lehi-ut.gov/government/meetings-and-agendas/` and `https://www.lehi-ut.gov/government/public-meetings/`
- Third-party transcript mirror: `https://lehi.openutah.org/` (OpenUtah — searchable transcripts; useful cross-check, not authoritative).

**No Legistar API.** Tested `https://webapi.legistar.com/v1/lehi/events` → `"LegistarConnectionString setting is not set up ... for client: lehi"`. So this is **Granicus Media/ViewPublisher only**, not Legistar. Retrieve by scraping the ViewPublisher HTML.

### URL / retrieval pattern (verified)
- `ViewPublisher.php?view_id=1` is one combined table for **all** bodies (City Council, City Council Work Session, Planning Commission, Local Building Authority, RDA, budget meetings, joint sessions). Each row carries a `clip_id` and, where minutes exist, a **Minutes** link:
  `//lehi.granicus.com/MinutesViewer.php?view_id=1&clip_id=<id>&doc_id=<uuid>`
- **MinutesViewer.php is a 302 redirect** → `DocumentViewer.php?file=lehi_<hash>.pdf&view=1`, which serves the actual **born-digital PDF**. Follow redirects:
  `curl -sL -A "Mozilla/5.0" -e "https://lehi.granicus.com/ViewPublisher.php?view_id=1" "<MinutesViewer URL>"`
  (Without `-L` you get a 14-byte `Redirecting...` stub. A browser UA + Referer is safest.)
- Agendas use `GeneratedAgendaViewer.php` / `AgendaViewer.php`; agenda packets and RDA docs are also plain `DocumentViewer.php?file=lehi_<hash>.pdf`.

### Coverage / format
- **Minutes years available: 2020 → present (2026).** ViewPublisher lists continuous coverage back to Feb 2020. (Pre-2020 fallback if ever needed: Utah Public Notice site `utah.gov/pmn`, body id **2512** = "Lehi City Council".)
- **Format: born-digital text PDF** (Word→PDF; clean `pdftotext -layout`). NOT scanned/OCR, NOT Granicus HTML minutes. Save originals to `raw/`, extract text layer.
- **Meeting cadence/weekday:** City Council **regular meetings = 2nd & 4th Tuesdays, 7:00 PM** (Pre-Council as early as 4:30 PM same day). **Work Sessions = 2nd Monday, 4:00 PM.** Council Chambers, 153 North 100 East. Schedule PDFs: `https://www.lehi-ut.gov/media/bj4pulli/2026-city-council-meetings.pdf` (and prior-year equivalents).

### Roll-call votes in minutes? — **YES, explicit named roll calls.** (verified)
Confirmed on City Council minutes clip 947 (Regular Meeting Jan 27, 2026, doc_id `d4b28fd7-1d6f-11f1-bb28-005056a89546`). Council minutes use this exact template:
```
Motion:          Councilor Stallings moved to ... Councilor Freeman seconded the motion.
Roll Call Vote:  YES: Councilor Freeman, Councilor Harrison, Councilor Lockhart,
                 Councilor Newall, and Councilor Stallings. The motion passed unanimously.
```
Mover + seconder + member-by-member YES/NO list, every action item. **Highly parse-friendly.** (Planning Commission minutes use a parallel format: `Vote: Commissioner Jones, yes. ... Motion passed with four in favor, one against.`)

---

## 2. Council structure — confirmed

- **Six-member form of government:** Mayor + **5 Council Members**, **all elected at-large** (0 districts, 5 at-large seats). Four-year **staggered** terms (≈3 seats then 2 seats alternate cycles).
- **Mayor:** presides; does **not** vote as a normal council member (votes only to break ties under Utah six-member city rules). For roll-call extraction treat Mayor as non-voting; he appears under "Members Present" and runs public hearings.
- Source: `https://www.lehi-ut.gov/government/mayor-and-council/` and `.../elected-officials/city-council-meetings/`.

**Current officials (terms from minutes + city page):**
| Name | Role | Seat type | Term ends |
|---|---|---|---|
| Paul Binns | Mayor | at-large | Jan 2030 |
| Rachel Freeman | Council Member | at-large | Jan 2030 |
| James Harrison | Council Member | at-large | Jan 2030 |
| Emily Lockhart | Council Member | at-large | Jan 2028 (interim) |
| Heather Newall | Council Member | at-large | Jan 2028 |
| Michelle Stallings | Council Member | at-large | Jan 2028 |

(Minutes also refer to members as "Councilor <Lastname>".)

---

## 3. RDA / development — **SEPARATE RDA meetings exist** (high value)

- Lehi has a **Redevelopment Agency (RDA)** with its own agendas/minutes, but business is run as a **recess/adjournment of the City Council into RDA session** (council adjourns, reconvenes as RDA, then back). So RDA docs are **separate documents on the same Granicus portal**, listed as **"Lehi City RDA Meeting"** rows in `ViewPublisher.php?view_id=1`.
  - Example RDA agenda/minutes docs:
    `https://lehi.granicus.com/DocumentViewer.php?file=lehi_6948eb6a1446ed1cedffdb462fdc8135.pdf&view=1` (RDA Mtg Aug 26, 2025)
    `https://lehi.granicus.com/DocumentViewer.php?file=lehi_c5439865eb90aff2b3f09dbf2a87b726.pdf&view=1` (RDA Mtg Mar 18, 2025)
- Active CRA project areas (follow-the-money): **Skye View CRA**, **Morning Vista CRA**, **Thanksgiving Point Housing Transit Reinvestment Zone (HTRZ)**. Plan/budget PDFs live under `lehi-ut.gov/wp-content/uploads/` and `lehi-ut.gov/media/` (e.g. `Skye-View-CRA-Plan-Draft-Rev-Aug-26-2025.pdf`).
- **Local Building Authority (LBA)** — the MBA equivalent — also has its own ViewPublisher rows (e.g. May 2024, May 2025).
- **Retrieval:** scrape ViewPublisher rows whose meeting name contains `RDA` / `Building Authority`; they carry the same `MinutesViewer`/`DocumentViewer` links as council. Treat RDA + LBA as separate bodies in the dataset.

---

## 4. Public comments

- **eComment portal (Granicus eComment / SpeakUp)** — confirmed present: ViewPublisher HTML loads `ecomment.buttons.js`, `EcommentsLink`, `eComment/Register`, and `SpeakUp` references. Each meeting row on `ViewPublisher.php?view_id=1` exposes an **eComment** button next to its agenda. Public submits **written comment before noon on meeting day** via that eComment link.
- City instructions: `https://www.lehi-ut.gov/government/meetings-and-agendas/` ("select eComment next to the Agenda below"; council items may also be **emailed directly to elected officials**).
- In-person: 3-min "Citizen Input" + public hearings; rules at `https://www.lehi-ut.gov/wp-content/uploads/2024/01/Citizen-Speaker-Rules.pdf`.
- **Where submitted comments surface:** (a) the Granicus eComment register/report per meeting (need to open a specific meeting's eComment page to confirm public visibility of submissions), and (b) transcribed/summarized inside the **minutes PDFs** (public-hearing comments are recorded by speaker name). Agenda **packets** (`DocumentViewer.php` packet docs) may also carry written-comment attachments.
- **Most promising URLs for the auditor:** the per-meeting eComment links off `ViewPublisher.php?view_id=1`; minutes PDFs (public-hearing sections); agenda packets. Do NOT pre-conclude availability — open a recent meeting's eComment page.

---

## 5. Elections — run by **Utah County**

- **Sources:**
  - `https://vote.utahcounty.gov/home` (Utah County election portal; results section — scrape index for hashed CSVs under `/cms/uploads/` as in playbook).
  - `https://electionresults.utah.gov/` (Enhanced Voting; state portal). 2025 Lehi example:
    `https://electionresults.utah.gov/results/public/utah-county-ut/elections/general11042025/...` (Lehi City Council ballot item).
  - Legacy county pages (e.g. `utahcounty.gov/dept/clerkaud/elections/2021RankedResults.asp`) now **404** — superseded by the two portals above.
- **Ranked-Choice Voting:** Lehi **used RCV in 2021 and 2023** municipal elections; **did NOT use RCV in 2025** (returned to traditional primary+general). RCV info: `https://www.lehi-ut.gov/government/elections/rcv/`. Per-round RCV visualizations: `https://rcvis.com/ve/21g_le_cc_2_u2` (2021 Council Seat 2; sibling URLs for other seats/years). **2023 RCV had a mid-count candidate withdrawal (Corey Astill) + recount** — flag tabulation quirks.
- **District vs at-large:** council elections are **at-large** (citywide), seats numbered (e.g. "City Council 1st Seat / 2nd Seat"), NOT geographic districts. Mayor elected citywide. Relevant cycles 2019/2021/2023/2025 (+ 2027).
- **Existing Desktop archive:** `~/Desktop/utah-elections-archive/counties/utah/` exists but is **scaffolding only** (`raw/ data/ geo/ maps/ scripts/` dirs, README says Utah County is "scaffolding next") — **no Lehi council/mayor race files yet**. The Lehi races (2019/21/23/25) are **NOT yet covered**; downstream will need to pull them from the two portals above (and handle 2021/2023 RCV round data + 2025 non-RCV).

---

## 6. GIS / boundaries

- **No council districts** (all at-large) → there is **no Lehi council-district GIS FeatureServer** to find; downstream geo is **"in city limits" only** (St. George / Vineyard pattern: single municipal-boundary polygon, point-in-polygon membership rather than district assignment).
- Boundaries to use:
  - **UGRC Municipal Boundaries** (statewide Utah Municipalities layer) → clip the **Lehi** polygon. (opendata.gis.utah.gov / UGRC `Boundaries/MunicipalBoundaries` FeatureServer.)
  - **UGRC VistaBallotAreas** FeatureServer filtered **CountyID = 25 (Utah County)** for voting precincts (matches the elections archive `fetch_geometry.py` pattern — change the CountyID constant to 25).
- `boundaries_available: true` (city-limits + precincts); `districts_or_atlarge: at-large` (no districts).

---

## Retrieval plan (recommended approach + effort)

| # | Dataset | Approach | Effort |
|---|---|---|---|
| 1 | **Council minutes 2020–present** | Scrape `ViewPublisher.php?view_id=1` → for each row with a `MinutesViewer` link whose meeting name = City Council (incl. Work Session, Budget, Amended, Joint), `curl -L` (browser UA + Referer) the redirect to the DocumentViewer PDF → save to `raw/`, `pdftotext -layout` → markdown. Filter to *minutes* only (skip Agenda/Packet links). | **Low–Med** — single combined table, clean text PDFs, no API but no auth either. Main work = parsing the ViewPublisher table to map clip_id→meeting name→date→Minutes link. |
| 2 | **Roll-call votes** | Regex over minutes text: `Motion:` (mover) + `seconded` + `Roll Call Vote:\s*YES:` / `NO:` member lists + `passed/failed`. Very regular template. | **Low** — best-case parse target; explicit named YES/NO. |
| 3 | **RDA + Local Building Authority minutes** | Same scrape; select rows named `RDA` / `Building Authority`; store as separate bodies. Also harvest CRA plan/budget PDFs under `lehi-ut.gov/media|wp-content`. | **Low–Med** — fewer meetings, identical mechanics. |
| 4 | **Public comments** | Open a recent meeting's Granicus **eComment** page off ViewPublisher to confirm public visibility + capture format; also extract public-hearing comment blocks from minutes; check agenda packets for written-comment attachments. | **Med** — eComment export format unverified; needs hands-on of one meeting page. |
| 5 | **Elections (2019–2025)** | Scrape `vote.utahcounty.gov` results index (hashed `/cms/uploads/` CSVs) + `electionresults.utah.gov` per-contest pages for Lehi mayor/council; pull 2021 & 2023 **RCV round data** (rcvis.com sibling URLs as cross-check); 2025 is standard tabulation. Add to `~/Desktop/utah-elections-archive/counties/utah`. | **Med–High** — two portals, hashed filenames, RCV round structure + 2023 withdrawal/recount quirk. |
| 6 | **Geo** | UGRC Municipal Boundaries → Lehi polygon (point-in-polygon "in city limits"); optional VistaBallotAreas CountyID=25 precincts. No district layer. | **Low** — one polygon; reuse elections-archive `fetch_geometry.py` with CountyID 25. |

**Suggested order:** minutes (1) → votes (2) → RDA/LBA (3) → geo (6) → elections (5) → public comments (4).

## Risks / blockers
- **Granicus 302 + 14-byte stub:** must follow redirects with a browser User-Agent + Referer; bare `curl` returns `Redirecting...`. Possible intermittent bot filtering — keep UA/Referer, add light rate-limiting.
- **One combined ViewPublisher table for all bodies:** must reliably classify each row by meeting-name string (City Council vs Planning Commission vs RDA vs LBA vs Work Session vs Budget vs Joint). Misclassification risks mixing bodies. Recent rows skew Planning Commission, so don't assume row order = body.
- **No API (no Legistar, no PrimeGov JSON):** pure HTML scrape; if Granicus changes ViewPublisher markup the scraper breaks.
- **Doc_id required:** MinutesViewer needs both `clip_id` and `doc_id` (UUID) harvested from the same table cell — can't synthesize.
- **Pre-2020 not needed**, but if scope expands, fall back to `utah.gov/pmn` body id 2512.
- **Mayor non-voting:** vote parser must not count the Mayor as a member vote (tie-break only); he appears in "Members Present."
- **Elections:** 2021 & 2023 RCV produce round-by-round tables (different schema than 2025 single-count); 2023 had a mid-count withdrawal + recount → reconcile "official" vs "unofficial". Hashed CSV filenames on the county portal require index scraping. Utah County archive folder is empty of Lehi data today.
- **eComment visibility unconfirmed:** submissions may not all be publicly published; auditor must open an eComment page to verify before concluding.
