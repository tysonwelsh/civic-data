# meeting_minutes/ — Taylorsville City Council + RDA vote pipeline

Turns **150 council/RDA minutes** (2020-01-08 → 2026-06-03, CivicEngage Central) into
structured motions + votes. Entry point **`extract_votes.py`** (reads `minutes_index.csv`,
PURE deterministic — no LLM/network, resumable); validator **`validate_votes.py`** (writes
`votes/_validation_report.txt`). 13-column `all_votes.csv` schema
(`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`).

## What's here
- `minutes/<year>/<week-monday>/<date>_<slug>.md` — **150** minutes files. Council meets
  **1st & 3rd Wednesday** (a 6:00 PM Briefing + a 6:30 PM Regular meeting captured in **one
  combined doc** per meeting-day); the folder is keyed on that week's **Monday**. Indexed in
  `minutes_index.csv` (`source=civicplus`; `format` ∈ `pdf-text` (126) / `ocr` (24)).
- `raw/` — the retained source PDFs (never modified).
- `minutes_unrecovered.csv` — the **2 honest gaps** (both 2026, past the data max):
  2026-06-17 (minutes not yet approved/posted — only the agenda exists) and 2026-07-01
  (meeting CANCELLED; the portal doc is a 1-page cancellation notice). Never stubbed.
- `extract_votes.py` / `validate_votes.py` / `votes/<year>/<week>/<slug>.json` (resumable
  intermediates) / `roster.csv`.
- `fetch_new.py` lives at the **repo root** (it probes both datasets) — see the root CLAUDE.md.

## Validation summary (`validate_votes.py`)
**150 meetings · 613 motions** (Council 605 · RDA 8) **· 2,457 vote/placeholder rows ·
2,315 named · 2020–2026.** Off-roster names **0**; the corpus screener finds **0 fabricated
names** including all 24 OCR files. `f.tally[meeting_minutes]` 462/471 (98.1%) — see the
10 documented named-vs-printed mismatches below.

## Vote grammar — narrative-tally unanimous + named contested/RDA rolls
Every motion anchors on `MOTION: Councilmember X moved … seconded by Councilmember Y`
(RDA docs: `Board Member X MOVED … Board Member Y SECONDED`). The vote resolution takes
four shapes, all handled:
- **FORM A — tabular per-member roll call** (the modern form; unanimous AND contested):
  one member per line `Council Member Burgess  Yes` / `Chair Harker  Yes` then
  `The motion passed 4-1` → one row per named member, `names_recorded:true`.
- **FORM B — inline roll call** (2020–2021 form, and ALL RDA docs):
  `The vote was as follows: Burgess-yes, Armstrong-yes, … Cochran-yes` → each
  `Surname-yes|no` pair parsed, `names_recorded:true`.
- **FORM C — narrative tally-only** (no per-member names): `…seconded by Council Member
  Knudsen and passed unanimously.` / `The motion passed 5-0` with no member block →
  **`names_recorded:false`, one placeholder row, EMPTY member list**.

**CARDINAL RULE — never fabricate / no Present-fill.** On a FORM-C unanimous motion the
minutes take a genuine roll call but print only the tally, so the assenting **majority is
honestly unnamed**; the extractor leaves the ayes blank rather than filling them from the
`Present:` header. Named per-member rows therefore appear on **contested** motions and on the
FORM-A/B named rolls — **not** on narrative-unanimous motions. `result` and the numeric tally
are **verbatim as printed**; normalized outcome/tallies/type live alongside in `motions_std.csv`.

## The Mayor does NOT vote — Chair → member mapping
Mayor **Kristie Overson** PRESIDES and gives executive updates only — she **never
moves/seconds/votes** and appears in **0** vote rows. The presiding **"Chair" is one of the 5
councilmembers** (the chair rotates: `Chair Harker`→Harker, `Chair Cochran`→Cochran,
`Chair Barbieri`→Barbieri …), mapped to that member — **never** to the Mayor. **Max ordinary
tally = 5** (there is no 6th/mayoral vote). If the Mayor were ever recorded casting a vote it
would be captured faithfully and flagged `mayor_voted:true` (never invented) — no such event
exists in this corpus.

## Roster (`roster.csv`) — 7 members
Only these surnames map to a vote: current **Burgess (D1), Cochran (D2), Barbieri (D3),
Harker (D4), Knudsen (D5, 2022+)** + former **Dan Armstrong** (D5, 2020–2021) and **Brad
Christopherson** (D3, 2020). Barbieri succeeded Christopherson mid/late 2020 (14 rows in 2020,
full 2021 after the D3 special); Knudsen succeeded Armstrong from 2022. County/other-city
officials named in the narrative never map to a vote. Light difflib fuzzy-match repairs
OCR-garbled surnames (`Barbier/`→Barbieri, `Merdith`→Harker) to the roster; an unrecoverable
name is left **BLANK**, never guessed.

## `body` column — RDA (in-meeting board)
Default `Council`. The Council convenes as the **Taylorsville Redevelopment Agency** board
(in-meeting recess); those docs / motions are tagged `body=RDA` (**8 motions**) via
`meeting_body(title, slug)` (title/slug carrying "Redevelopment Agency"/"RDA"). RDA rolls are
FORM-B named and also cap at **5**. There are **no separate RDA portal files** to acquire —
the in-record captures are the complete published RDA record, not an acquisition gap.

## The mid-2025 RICOH-OCR switch
Taylorsville swapped minutes production to **scanned RICOH output mid-2025**, so the most
recent files (24 of 150; `format=ocr`) are image-only PDFs OCR'd at build time. The OCR is
clean — the corpus screener flagged **0** dict/split-word/weird-char outliers on all OCR
files, and no OCR file invented a name. Where OCR **dropped** a legible name (see below), the
extractor kept the surviving names and never fabricated the missing one. `fetch_new.py` is
OCR-aware (pdftotext -layout, Tesseract fallback) so new scanned minutes ingest the same way.
(Follow-up worth queuing: a PMN born-digital upgrade for these OCR files where PMN posts a
clean text-layer PDF for the same meeting — CivicEngage is the current authoritative source.)

## Known discrepancies (advisory; source-faithful, NOT corrected in place)
- **10 named-count vs printed-tally mismatches** (validator list): e.g. 2020-05-06 m3/m4/m6
  (printed 4-0, 3 names survived), 2021-06-16 m4/m5, 2021-11-17 m2, 2024-08-21 m2,
  2025-01-22 m5, 2026-03-04 m3 (printed 5-0, 4 named), plus 2021-03-03 m2 (correctly a 3-2 by
  orientation). All are OCR-dropped names or source typos where the extractor kept the legible
  names and never invented the missing one. Any correction belongs in `db/vote_overrides.csv`,
  never an in-place edit.
- **69 council motions carry `outcome=unknown` in `motions_std.csv`** — all have **blank
  `result_raw`**: the source printed no disposition (procedural/administrative items). An honest
  source limitation, correctly carried as `unknown`, not a parser miss.

## The recon folder-id correction (portal note)
`recon.md` listed the Council **Minutes** year-folder ids as 2020=151 … 2026=437 — those are
actually the **Audio Recordings / Agendas** column. The Council "Agendas & Minutes" landing
renders **three parallel year-folder columns** (Agendas | Minutes | Audio), so each year has
three `-folder-<N>` ids. The **true Minutes column** (verified: folder-150 for 2020 holds
docId 3943 = the built 2020-01-08 council minutes) is **2020=150, 2021=192, 2022=256,
2023=287, 2024=311, 2025=341, 2026=436**. `fetch_new.py` does not hard-code these — it takes
the first `-folder-<N>` per year in DOM order (= the Minutes column, verified live). A council
meeting-date lists **both** its agenda and its approved minutes under the same "Month D, YYYY"
label inside that folder; `fetch_new.py` resolves the genuine minutes doc by content
(recorded-motion prose), dropping agendas and cancellation notices.

## Run
```
python3 extract_votes.py     # writes votes/*.json then rebuilds all_votes.csv (resumable)
python3 validate_votes.py    # writes votes/_validation_report.txt
```
`all_votes.csv` is valid RFC-4180 (motion text contains commas/quotes — read it with a real
CSV parser, NOT `awk -F,`).
