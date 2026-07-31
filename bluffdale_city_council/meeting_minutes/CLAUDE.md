# meeting_minutes/ — Bluffdale City Council + in-session RDA/LBA vote pipeline

Turns **166 council minutes** (2020-01-06 → 2026-06-24, CivicPlus/CivicEngage
AgendaCenter, CID=2) into structured motions + votes. Entry point
**`extract_votes.py`** (reads `minutes_index.csv`, PURE deterministic — no
LLM/network, resumable); validator **`validate_votes.py`** (writes
`votes/_validation_report.txt`). 13-column `all_votes.csv` schema
(`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`).

## What's here
- `minutes/<year>/<week-monday>/<slug>.md` — **166** minutes files
  (`slug = council_<iso>_<docId>`). Council meets **Wednesday**; the folder is
  keyed on that week's **Monday**. Indexed in `minutes_index.csv`
  (`source=civicplus`; `format` ∈ `text` (137) / `ocr` (29)). The 137 `text`
  files include 2 born-digital Word `.docx` (converted via `textutil`); the 29
  `ocr` files are image-only scans (concentrated **2023–2026**, tesseract at 300
  dpi — the 2020–2021 docs are born-digital text, NOT scans).
- `raw/` — the retained source PDFs / .docx (never modified), named
  `council_<iso>_<docId>.pdf`.
- `extract_votes.py` / `validate_votes.py` / `votes/<year>/<week>/<slug>.json`
  (resumable per-meeting intermediates) / `roster.csv` (11 observed voters).
- `fetch_new.py` lives at the **repo root** (it probes both datasets) — see the
  root CLAUDE.md.

## Validation summary (`validate_votes.py`)
**166 meetings · 971 motions** (Council 872 · RDA 77 · LBA 22) **· 2,996
vote/placeholder rows · 2,538 named · 513 named motions / 458 tally-only ·
2020–2026.** Off-roster names **0**; printed-vs-counted tally mismatches **0**;
`CEILING CHECK (<=5 members/tally): PASS`. The JSON layer reconciles exactly to
the CSV (971 motions).

## The three bodies — Council + in-session RDA + LBA
The Council **adjourns and reconvenes in-session** as the **Redevelopment Agency
(RDA)** and the **Local Building Authority (LBA)** inside the **same combined
minutes PDF** (like SLC's four-body pattern). `extract_votes.py` walks the in-doc
section headers and tags each motion's `body`:
- `Council` (872 motions · 2,612 rows) — the default legislative body.
- `RDA` (77 motions · 300 rows) — the Redevelopment Agency board.
- `LBA` (22 motions · 84 rows) — the Local Building Authority board.

There is **no separate RDA/LBA category or portal** to acquire — the in-record
captures ARE the complete published RDA/LBA record.

## The Mayor — non-voting in Council, votes as Chair in RDA/LBA
Bluffdale is a **Mayor + 5 at-large council** city. In the **pure `Council`
body the Mayor is NON-voting**: an ordinary council roll call caps at **5**. The
Mayor casts a Council vote only on a genuine **tie-break** — there are **exactly
2** in the corpus, both faithful and both surfaced by the validator:
- **2022-11-09 motion 4** (Ordinance 2022-18, ADU text amendment): source prints
  *"Kallas-Aye; Crockett-Nay; Hales-Nay; Gaston-Aye; **Mayor Hall-Aye. The motion
  passed 3-to-2**"* — Mayor Hall breaks a 2-2 council tie (6th voter).
- **2025-05-14 motion 4**: source prints *"Wilding-Yes … Aston-Yes, **Mayor
  Hall-Yes. The motion passed 4-to-2**"* — a recorded 6th mayoral vote.

In the in-session **RDA and LBA** the **Mayor votes as Chair** (the board's
presiding member), so a named RDA/LBA roll caps at **6** and legitimately
includes the Mayor (e.g. 2020-06-10 RDA motion 8 names all 5 members + *Derk
Timothy* the mayor). The validator's "max MEMBER tally = 5 per body" counts the 5
non-mayor members separately; the mayor is the honest 6th where it appears.

## Roster (`roster.csv`) — 11 observed voters
Mayor **Derk Timothy** (2020–2021) → **Natalie Hall** (2022+). At-large members
across the window: **Wendy Aston, Traci Crockett, Dave Kallas, Jeff Gaston, Mark
Hales, Alan Lord, Steve Austin, Greg Wilding** (+ Mackey Smith from 2026). Only
these names map to a vote; county/other officials named in the narrative never
do. A roll-call name too garbled by OCR to resolve is left **blank**, never
guessed.

## Vote grammar — named inline rolls + narrative tally-only
Every motion anchors on `Council Member X moved … seconded by Council Member Y`.
Two vote shapes, both handled:
- **Named inline roll call** — `Vote on Motion: Council Member Kallas-Aye;
  Council Member Crockett-Nay; … The motion passed 3-to-2.` → one row per named
  member, `names_recorded:true` (513 motions).
- **Narrative tally-only** — `The motion passed with the unanimous consent of the
  Council` / `passed unanimously` with no per-member block → **one placeholder
  row, EMPTY member list, `names_recorded:false`** (458 motions).

**CARDINAL RULE — never fabricate / no Present-fill.** On a tally-only unanimous
motion the assenting majority is honestly **unnamed**; the extractor leaves the
ayes blank rather than filling them from an attendance header. `result` and the
numeric tally are **verbatim as printed**; normalized outcome/tallies/type live
alongside in `motions_std.csv` (971 rows).

## The partial-OCR seam (2023–2026)
Bluffdale switched some later minutes to **scanned production**, so 29 of 166
files (`format=ocr`, mostly 2023+) are image-only PDFs OCR'd at build time. OCR
is clean — the corpus screener flagged **0** stubs and no OCR file invented a
name. Where OCR dropped a legible name, the extractor kept the survivors and
never fabricated the missing one. `fetch_new.py` is OCR-aware (pdftotext -layout,
tesseract fallback) so new scanned minutes ingest identically.

## Run
```
python3 extract_votes.py     # writes votes/*.json then rebuilds all_votes.csv (resumable)
python3 validate_votes.py    # writes votes/_validation_report.txt + roster.csv
```
`all_votes.csv` is valid RFC-4180 (motion text contains commas/quotes — read it
with a real CSV parser, NOT `awk -F,`).
