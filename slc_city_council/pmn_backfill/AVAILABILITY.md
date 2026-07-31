# SLC PMN backfill — availability record

**As-of:** 2026-07-05 · **Checked by:** expand-city-sources Source 4 (Utah Public Notice cross-check) · **Scope window:** 2020–2026 (the repo's data floor)

## PMN entity + public-body IDs — CONFIRMED via the global chain

Resolved by walking `/pmn/list/entities.html?id=3&limit=2000` → SLC entity → its
`/pmn/list/publicBodies.html?id=<entity>&limit=2000`. Never guessed. Raw HTML of both
pages retained in `raw/slc_entities.html`, `raw/slc_bodies.html`.

| PMN body | ID | Notice history captured | Notices | Notices carrying a `(Meeting Minutes)` attachment |
|---|---|---|---|---|
| **Salt Lake City (entity)** | **259** | — | — | — |
| Salt Lake City Council | **1360** | 2011-01-11 … 2026-07-14 | 2,088 | 616 |
| Planning Commission | **1274** | 2008-09-23 … 2026-07-08 | 547 | 42 |
| Redevelopment Agency (RDA) | **1277** | 2008-09-09 … 2025-01-11 | 482 | 135 |
| Community Reinvestment Agency (CRA) | **9033** | 2025-05-12 … 2026-06-16 | 46 | 22 |
| Local Building Authority (LBA) | **3475** | 2011-11-01 … 2026-06-16 | 157 | 60 |

(Other SLC bodies exist on PMN — Historic Landmark Commission 1266, Board of Appeals
1264, etc. — but were out of scope for this council/PC/RDA-family backfill. The full
body list is in `raw/slc_bodies.html`.)

## What was checked
Each body's **complete** cumulative notice history was retrieved in one GET via the browse
endpoint `/pmn/list/notices.html?id=<bodyId>&page=400` (a high page number returns the
saturated list — verified by the date ranges above reaching back to 2008–2011). Every
notice's attachments were parsed for the `(Meeting Minutes)` type label
(`parse_notices.py` → `raw/notices_<id>.json`), and each minutes-bearing **meeting date
was read from inside the PDF** (notice date ≠ meeting date in general; for SLC council
minutes they happened to coincide exactly — see below) and set-differenced against the
repo's audited minutes indexes (`meeting_minutes/minutes_index.csv`,
`planning_commission/minutes_index.csv`), tolerance ±4 days.

## What was recovered (additive — see `index.csv`, `coverage.md`)
**7 council minutes documents** absent from the audited minutes layer were downloaded,
text-extracted (`text/`, `pdftotext -layout`, all born-digital / screener-clean), and indexed:

- **2021-09-14** Work Session + Formal Meeting (repo has 09-07 and 09-21 only)
- **2022-08-29** Special Limited Formal Meeting (repo has 08-16 only). **CORRECTION 2026-07-19:**
  this PMN file (913093) is *not* the Truth-in-Taxation session — its body is the **6:20 pm
  Budget-Amendment-No.1 / Other Side Village consent / closed-session** meeting (approved
  Nov 10, 2022 = PrimeGov template 2920). The **actual Truth-in-Taxation** hearing that
  evening was a *separate*, earlier session (6:05–6:15 pm, approved Oct 18, 2022 = PrimeGov
  template 2955), which PMN never carried. Both are now ingested from born-digital PrimeGov
  into the audited layer — see the 2026-07-19 note below.
- **2024-01-02** Oath of Office Ceremony (repo starts the year at 01-09)
- **2026-01-05** Oath of Office Ceremony (repo starts the year at 01-13)
- **2020-06-09** Formal Meeting and **2020-06-16** Formal Meeting — the repo held only the
  *Work Session* minutes for these two dates; PMN carried the same-day Formal minutes,
  which the repo entirely lacked.

**RDA / CRA / LBA: 0 in-scope recoveries.** Every in-scope RDA/CRA/LBA minutes date on PMN
falls on a date the SLC council minutes already cover — consistent with SLC's practice of
adjourning/reconvening the Council *in-session* as RDA/CRA/LBA inside one combined minutes
document. PMN registers them as separate bodies, but their minutes dates are a subset of
the council series. **Planning Commission: 0 in-scope recoveries** (PMN only began carrying
PC minutes attachments in 2023, and every one matches a repo PC minutes date).

## Secondary goal — 2020 minutes source-URL recovery (see `url_recovery_2020.csv`)
The repo's **68 Laserfiche-sourced 2020 council minutes** carry **no `source_url`** in
`meeting_minutes/minutes_index.csv` (per-doc DocView URLs live only in
`meeting_minutes/index_laserfiche.csv`). PMN's 2020 council notices carry the same minutes
as `/pmn/files/<id>.pdf`. All 68 PMN 2020 council minutes-attachment PDFs were downloaded
(`raw/2020/`, 12 MB), and their meeting date + session type were read from the PDF text and
matched to the repo rows:

- **65 of the 68** un-URL'd 2020 repo minutes files now have a recovered, citable PMN URL
  (exact meeting-date match, session type verified in PDF header — `pdftotext` confirmed
  `notice_date == meeting_date` for all 68).
- **3** (the 2020-01-07, 01-17, 01-21 **Formal** minutes) have **no PMN source** — PMN
  posted only the Work Session minutes for those three dates. Recorded honestly with a
  blank `pmn_url`.
- 1 PMN attachment labelled `(Meeting Minutes)` (`593695`, "April21 F.pdf", 2020-04-21) is
  in fact the **agenda**, not minutes — detected by reading the PDF and **excluded** from
  both `index.csv` and the URL recovery.

## What is NOT here (honest gaps / deliberate exclusions)
- **Pre-2020 PMN minutes** (council back to 2016, RDA/LBA back to 2011) are below the
  repo's 2020 floor and were not downloaded — they are enumerated in
  `raw/notices_<id>.json` if ever wanted.
- **PMN purges older attachment blobs.** No in-scope minutes attachment 404'd on this run
  (every `raw/_fetch_log.jsonl` line is `status:200`), so there are zero
  `source-unavailable` rows — but the risk is real for future refreshes.
- **The 2020-01-07/17/21 Formal minutes** are not on PMN. (The *second* 2022-08-29 doc that
  the repo's *Laserfiche harvest* index once listed but never fetched was **resolved
  2026-07-19**: it is the Truth-in-Taxation session, template 2955 — both 2022-08-29
  sessions are now ingested from born-digital PrimeGov, see the note below; neither is on PMN
  as a distinct file.)
- **PMN historical search is POST-only** (`/pmn/searchresult.html`, CSRF-gated) — disallowed
  by the polite-GET rule. Full enumeration used the **GET** cumulative browse endpoint, which
  returns each body's complete history, so no coverage was lost.
- **PMN is a pre-meeting NOTICE service, not a minutes archive.** The authoritative SLC
  minutes source remains **Laserfiche/webdme**; PMN's role here is a gap-filler + a citable
  public mirror for the un-URL'd 2020 set.

## Provenance
Raw bytes + SHA-256 + HTTP status for every fetch: `raw/_fetch_log.jsonl` (crawl + 7
recovered docs) and `raw/2020/_fetch_log.jsonl` (the 68 URL-recovery PDFs), both written by
`scripts/polite_fetch.py` (browser UA, GET-only, ≥1 s throttle). Parser + cross-check +
verification code: `parse_notices.py`, `crosscheck.py`, `verify_2020_minutes.py`,
`build_url_recovery.py`. Full parsed notice inventories: `raw/notices_<bodyId>.json`.

## 2026-07-19 — 2022-08-29 double-document disambiguation + ceremonial-doc ruling

**The Q3 refresh found TWO distinct same-date, same-title PrimeGov docs for the 2022-08-29
"Special Limited Formal Meeting"** — template **2955** (1 vote) and template **2920** (5
votes) — both absent from the audited layer, deferred pending disambiguation. Resolved by
**in-body evidence** (not portal labels):

- **VERDICT: two genuinely separate, sequential sessions the same evening** (the west_jordan
  work-session precedent) — ingest BOTH.
  - **2955** — called to order **6:05 pm**, adjourned **6:15 pm**, approved **Oct 18, 2022**,
    signed Special Meeting Order attachment **21664**. Agenda = the **FY2022-23
    Truth-in-Taxation public hearing** only (public comment from Rusty Cannon, George Chapman,
    Michael Bills, Sandra Chacon), **1 motion** (close hearing + adopt final tax-levy
    ordinance, Mano/Wharton, 7-0).
  - **2920** — called to order **6:20 pm**, adjourned **6:40 pm**, approved **Nov 10, 2022**,
    signed Special Meeting Order attachment **21665**. Agenda = **Budget Amendment No. 1**
    (reconsider + continue hearing) + **Other Side Village** consent (1850 W Indiana) +
    **closed session**, **5 motions** (7-0/7-0/7-0/6-0/7-0).
  - **Evidence of separateness:** non-overlapping times (6:05–6:15 then 6:20–6:40); disjoint
    agendas; **zero motion overlap**; different approval dates (Oct 18 vs Nov 10); different
    signed Special Meeting Orders (21664 vs 21665). Neither is an amended/superseding copy of
    the other.
- **Ingested** into `meeting_minutes/minutes/2022/2022-08-29/` as born-digital PrimeGov
  (`source=primegov`, `provenance=minutes`, `> Source:` headers), slugs
  `special-limited-formal-meeting-truth-in-taxation` (2955) and
  `special-limited-formal-meeting-budget-amendment` (2920). Votes extracted by direct read
  (no API); **6 motions / 42 member-vote rows**, all tallies cross-checked 6/6. The
  born-digital 2920 **supersedes** the PMN OCR copy (file 913093) in the audited layer; the
  PMN file is retained here as the historical recovery record only.

**Ceremonial / out-of-scope docs (same title-filter class) — ruled DO-NOT-INGEST, recorded
in `pmn_exceptions.csv` so the quarterly scan does not re-surface them:**
- **3 Oath-of-Office Ceremony** docs with HTML Minutes — 2022-01-03 (PrimeGov tid 2625),
  2024-01-02 (tid 3388), 2026-01-05 (tid 3953): ceremonial swearing-in, no governing votes.
  (The 2024 + 2026 files are staged in `index.csv` as PMN recoveries but were never promoted
  to the audited layer — correctly excluded.)
- **Redistricting Advisory Commission** (2022 series; HTML Minutes on 2022-02-24 tid 2717 and
  2022-03-17 tid 2750): an advisory commission, out of the Council + land-use-PC scope this
  repo tracks (same rationale as Historic Landmark Commission). Also excluded by the
  scraper's `BODY_RE` title filter, which matches neither "Oath of Office Ceremony" nor
  "Redistricting Advisory Commission".
