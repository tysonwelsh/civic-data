# Weber County — source reconnaissance (2026-07-20)

The repo's **second COUNTY entity** (after salt_lake_county) and the first county built
from **prose minutes with NAMED roll-call votes** rather than a Legistar API. Weber County
(FIPS 49057; fed_index 103) governs by a **3-member Board of Commissioners** (a
Council-of-Commissioners form, NOT Council-Mayor) — no separately-elected executive.
Contains the repo's ogden_city_council. Meets **Tuesdays, 10:00 a.m.**, Weber Center,
2380 Washington Blvd., Ogden. Counties are modeled as **modules**, not big cities.

## Governance & the voting body

- **Board of County Commissioners — 3 members**, all voting; one serves as **Chair**, one
  as **Vice Chair** (elected internally each January — see the first meeting of each year).
  Current board (2023– ): **Gage Froerer** (Chair), **James "Jim" H. Harvey** (Vice Chair),
  **Sharon Bolos**. Prior-era commissioners appear in the minutes across 2015–2022
  (e.g. Ebert, Gibson, Jenkins, Bell, Ivie) and are captured data-first from the roll calls.
- The Commission is the county's legislative + executive body; there is no county council
  and no elected mayor. Agencies (RDA, etc.) convene in-session as the same Commission.
- County Clerk/Auditor's office takes the minutes (Ricky Hatch, Clerk/Auditor).

## Legislative — Board of Commissioners minutes ✅ primary source found

- **Platform: a self-hosted "Transparency" portal** (NO API, NO Legistar/Granicus).
  - Recent index: `https://www.webercountyutah.gov/Transparency/commission_meetings.php`
    — direct links to born-digital PDFs.
  - Full archive (2000→present): `https://www.webercountyutah.gov/Transparency/commission_minutes_archive.php`
    — `minutes_view.php?minute_id=<N>&id=1` detail pages, each resolving to the PDF.
  - Born-digital PDFs at `https://www.webercountyutah.gov/commission/documents/minutes/min_MMDDYYYY.pdf`
    (revisions/second postings carry a `_2` suffix, e.g. `min_03242026_2.pdf`).
  - Agendas are posted as Word docs; meeting video is on YouTube (not harvested).
  - **Utah Public Notice (pmn.utah.gov) body 2167** mirrors notices — a backfill / cross-check
    channel, not needed within the floor (the county's own PDFs are complete and born-digital).
- **Harvest strategy — UNION of both indexes.** Neither index alone is complete for 2015+:
  `commission_meetings.php` carries ~484 dated PDFs (incl. `_2` revisions) and
  `commission_minutes_archive.php` carries ~524 dated `minute_id` entries; ~49 dates are
  archive-only and ~9 (recent 2025) are portal-only. `db/fetch_minutes.py` merges them,
  resolving archive-only `minute_id`s to their real PDF, then `pdftotext -layout` →
  `legislative/minutes/<year>/<date>_commission.md` (provenance front-matter) +
  `legislative/minutes_index.csv`. Genuinely-unrecoverable dates → `minutes_unrecovered.csv`.

## The vote-recording CEILING — NAMED roll call, even on unanimous motions

Weber minutes name **every commissioner's individual vote on every recorded motion**, unlike
the tally-only county councils. The grammar is highly regular and machine-anchorable:

> APPROVAL OF RESOLUTION 12-2026 OF THE COUNTY COMMISSIONERS OF WEBER COUNTY …
> Commissioner Harvey moved to approve Resolution 12-2026 …; Commissioner Bolos seconded.
> **Chair Froerer – aye; Commissioner Harvey – aye; Commissioner Bolos – aye**

Roll-call lines optionally carry a `Roll Call Vote:` prefix; the separator is an en-dash or
hyphen; values seen: **aye / nay / abstain / absent / recuse / excused**. This is a NAMED
ceiling, not a tally ceiling — so Weber's `motion`/`vote` layer comes straight from the
minutes prose (`db/extract_votes.py`), and `names_recorded=1` is the norm. A motion whose
minutes printed no roll call gets `names_recorded=0` (honest gap, never fabricated). There is
no separate "Motion carried 3-0" result string — **`result_raw` is the verbatim roll-call
line**; `outcome` (Pass/Fail) is derived from the aye/nay tally.

## Resolution / ordinance / contract numbers (for later ordinance linkage)

Numbered instruments are printed inline with their motions and are captured to
`db/staging/motion_refs.csv` (columns: meeting_date, motion_no, ref_type, ref_number,
verbatim), keyed to the extracted motion:
- **Resolutions:** `Resolution NN-YYYY` (e.g. `Resolution 12-2026`, `13-2026`, `16-2026`).
- **Ordinances:** cited by subject + **reading stage** (`First Reading` / `Final Reading`,
  stored on `motion.stage`); a formal ordinance number is assigned at final adoption.
- **Contracts/agreements:** occasional `X-YYYY-NNNN`-style identifiers.
These feed the (separately-owned) `ordinances/` module's enacting-vote linkage.

## Work sessions / meeting types

The portal posts one "Commission Minutes" document per meeting date (no duplicate-date
entries in the archive). Where a posted document's **title block** self-identifies as a
**work session** (e.g. "WORK SESSION OF THE BOARD OF COMMISSIONERS"), `fetch_minutes.py` tags
`meeting_type=work_session` and `build_db.py` routes it to a distinct `Board of Commissioners
Work Session` body so the body/meeting-type distinction is preserved; regular meetings are
`Board of Commissioners`. **3 work sessions** fall in the floor (2016-07-06, 2016-07-13,
2018-10-10) — all discussion-only (0 motions). Detection is title-block-only on purpose:
regular meetings routinely *mention* "work session" in discussion prose (2021-01-05,
2024-03-19 initially mis-flagged, then corrected). Public hearings are convened in-session
(the Commission adjourns/reconvenes within the same minutes doc) and their motions are
captured like any other.

## Extraction findings & ceilings (for the closing/audit pass)

- **TWO roll-call grammars** — both handled by `db/extract_votes.py`:
  (a) modern single line, semicolon-separated, dash-joined ("Chair Froerer – aye; …");
  (b) EARLY-ERA (mostly 2015–2017): a `Roll Call Vote:` header then ONE member per line
  joined by dot leaders ("Commissioner Bell .......... aye"). Missing grammar (b) was the
  cause of the initial unnamed-motion cluster; it is now parsed.
- **A motion's roll call can sit pages below the motion** (post-discussion) — the scanner
  reads forward up to the NEXT motion, so long-debated items (e.g. the 2020-01-07 rezone that
  FAILED 1–2 under the unanimous-vote rezone rule) are captured, while genuinely unvoted
  motions never steal the following motion's roll call.
- **"Freorer" (23 votes, 2 meetings 2023-01-10/24) is a source misspelling of "Froerer"** —
  retained verbatim (never overwritten); it needs a **person alias override** in the closing
  pass to merge into Gage Froerer.
- **Joint Weber+Davis boundary meetings** (2020-10-14, 2023-08-01) print BOTH boards' roll
  calls (sometimes intermixed on one line). Davis commissioners **Kamalu / Stevenson** are
  excluded from Weber votes (documented `VISITING` set in the extractor); "Elliott" is left
  ambiguous (Davis Comm. Randy vs Weber Surveyor Max) but cast no vote.
- **15 motions are honestly `names_recorded=0`** (0.35%): a lost-for-lack-of-second motion, a
  recess "saunter" motion, a source-malformed roll (a commissioner printed with no value),
  and stacked organizational motions sharing one roll call. Genuine ceilings, not misses.
- **Resolution / ordinance / contract numbers** are captured to `db/staging/motion_refs.csv`
  (**1,148** rows — 749 resolutions, 399 ordinances, 0 contracts; count refreshed 2026-07-26 after the image-only-scan OCR backfill. The old "1,679 / 1,096 / 582 / 1" figure never matched the file), keyed by (meeting_date,
  motion_no); ordinance reading stage lands on `motion.stage`. This is the join surface for
  the (separately-owned) `ordinances/` module's enacting-vote linkage.

## Pre-floor depth recorded for a future backfill

Data floor is **2015-01-01**. The archive's born-digital depth reaches back to **2000** — a
high-value future backfill (all named roll calls, same grammar). Archive meeting counts per
pre-floor year (for the backfill scope): 2000: 32, 2001: 49, 2002: 43, 2003: 48, 2004: 46,
2005: 48, 2006: 49, 2007: 50, 2008: 49, 2009: 49, 2010: 49, 2011: 49, 2012: 46, 2013: 46,
2014: 39 (≈ 690 additional meetings). Logged here; not harvested in this build.

## Module status

| module | source | owner / status |
|---|---|---|
| `legislative/` | County Transparency portal (Commission minutes PDFs, 2015+) | THIS build — harvest → extract → db |
| `db/` | prose extraction → weber_county.db (standard 8-table schema) | THIS build |
| `land_use/` | County + Ogden Valley / Western Weber Planning Commissions | separate agent |
| `plans/`, `projections/`, `ordinances/`, `gis/`, `elections/` | various | separate agents |
