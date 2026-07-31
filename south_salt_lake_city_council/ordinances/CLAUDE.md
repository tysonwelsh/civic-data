# ordinances/ — South Salt Lake adopted-ordinance index + linkage (as-of 2026-07-13)

Additive dataset built by the `expand-city-sources` skill (Source 3). **Read-only** on every
existing dataset — nothing here modifies `meeting_minutes/`, `planning_commission/`, `db/`, etc.

## What this is
An index of **adopted South Salt Lake City ordinances, 2020→present** (114 rows), each mapped —
where the recorded minutes allow — to the council **motion** that adopted it in
`meeting_minutes/all_votes.csv`, with an honest confidence score. **39 of 100** enumerated
ordinances are **land-use** (Title 17 / zoning-map / general-plan / subdivision / overlay /
right-of-way). Window: **2020-01-08 … 2026-06-17**.

## Code host (recorded fact)
**Codifier = Municode** — `library.municode.com/ut/south_salt_lake`, client **4410**, product
**16638** ("Code of Ordinances"), codified through **Ord. No. 2026-03 (2026-01-28)**,
Supplement 68. The library page is a JS SPA, but the **Municode NEXT API (`api.municode.com`)
is openly reachable, GET-only, no auth** — the source of this dataset. Municode serves the
**current consolidated code text, not per-ordinance PDFs**; its **OrdBank** (pending-ordinance
PDFs) is empty (`newOrdCount=0`).

## Where the data comes from (and why it is shaped this way)
There is **no online archive of individual signed SSL ordinance PDFs** (verified — see
`AVAILABILITY.md`: PMN body 1295 is minutes-only; DocumentCenter has no ordinance folder;
AgendaCenter packets hold only drafts; American Legal is 403). So the backbone is the
**Municode "Code Comparative Table and Disposition List"** (`nodeId=COCOTADILI`) — an
authoritative, **minutes-independent** chronological table giving every ordinance's
**Number, adoption Date, Description, and Code Section**. Retained raw JSON in `raw/`
(via `polite_fetch.py`, `_fetch_log.jsonl` provenance); born-digital text sidecars in `text/`.

This makes SSL's number→date→subject map a genuine **cross-source** enumeration (unlike Lehi's
minutes-derived index) — but the *linkage to votes* is still thin because of the coverage cliff.

## raw/ and text/
- `raw/municode_cocotadili_comparative_table.json` — the disposition table (the enumeration source).
- `raw/municode_orlidita_legacy_ordinance_table.json` — legacy pre-Supplement-20 table (provenance).
- `raw/municode_clientcontent_4410.json`, `raw/municode_latest_job_16638.json` — product/supplement metadata.
- `text/*.txt` — born-digital `Municode API HTML→text` sidecars of both disposition tables
  (feed `cities.db fts_ordinance`). `screen_corpus.py` = clean (no garble/mojibake/stubs; the
  `repeated_line` flag is benign — repeated disposition-cell values "Added"/"Not included"/"Rpld").

## index.csv columns
SCHEMA_SPEC §9 ordinances contract (exact order) —
`ordinance_no,adoption_date,date,title,source_url,retrieved_date,format,extraction_method,path,
land_use,result,matched_motion_date,matched_motion_no,match_confidence` — then city extras:
- `code_section` — the Municode "Section this Code" (Title 17.* ⇒ land use; "Not included" ⇒ uncodified).
- `adoption_date_raw` — the table's verbatim `M- D-YYYY` date string (normalized into `adoption_date`).
- `codified` — yes / no ("Not included" rows: budget, some zoning-map amendments).
- `linkage_note` — why the confidence is what it is.
- `minutes_source` — the recorded-minutes table joined against, for linked rows.
- `format` = `json` (born-digital API); `result` is **blank** — adoption is implied by
  codification, NOT asserted from a roll call (SSL prints no result string; a real tally only
  exists where a recorded motion links — read it from `all_votes.csv` via `matched_motion_*`).

## Linkage method + confidence (the coverage cliff governs this)
SSL council motions **cite ordinances by subject, never by number** (0 `#YYYY-NN` tokens in
`all_votes.csv`), so linkage is by **adoption date + cited code section / subject**, never by
number. The matcher, per adoption date, considers only **ordinance-adopting** council/RDA
motions (motion text mentions an ordinance; deferrals — "move to Unfinished Business" — and
procedural motions — minutes/adjourn/consent — are excluded, so an ordinance is never
false-matched to a minutes-approval motion):
- **high (0)** — date+number in a motion. **Not producible** (SSL motions carry no number).
- **medium (1)** — an adopting motion on the date whose **cited code section matches** the
  ordinance's section. Ord **2025-06** (Standard road profile for Haven Ave, §17.10.120) ↔
  the 2025-03-12 motion "Amending Section 17.10.120".
- **low (3)** — a recorded ordinance-adopting motion exists on the adoption date, but the
  specific ordinance can't be confirmed because the motion text is **truncated at the item
  title** in `all_votes.csv` (2020-09 TTBU, 2020-11 meetings-of-council, 2025-05 short-term rentals).
- **none (96)** — no recorded adopting motion on the adoption date. This is the **coverage
  cliff**: SSL's recorded council minutes exist essentially only for 2020–early-2021 + sporadic
  recent meetings (253 agenda-only council dates in `meeting_minutes/minutes_unrecovered.csv`).
  The ordinance was adopted; the *minutes recording it were never published*. Honest, not a miss.
- **within_source (14)** — ordinances the **minutes prove** were adopted but Municode has **not
  yet codified** (all 2026-06-17 FY2026-27 budget/tax ordinances, adopted after the 2026-01-28
  codification cutoff). SSL motions carry no number, so `ordinance_no` is **blank** (= not
  recorded, never invented); `title` is verbatim motion text (several are the bare adopting
  phrase because the extractor separated the agenda-item subject onto another row).

**No match was ever forced.** Mayor is **non-voting** (max council roll 7); no linkage treats
the mayor as a voter.

To read an ordinance's full current text: open the Municode code at its `code_section`. To read
an adopting vote: filter `meeting_minutes/all_votes.csv` on `matched_motion_date` + `matched_motion_no`.

## Rebuild
`python3 build_ssl_ordinances.py` (idempotent; helper lives inside this dir). Re-fetch the raw
Municode JSON with `polite_fetch.py` when the code is re-supplemented (bump the `jobId` from
`api.municode.com/Jobs/latest/16638`), then re-run.
