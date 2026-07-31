# packets/ — agenda packets & staff reports (Murray)

Additive dataset built by the `expand-city-sources` skill (source #1), 2026-07-13.
**Does not modify any existing dataset.** Read `AVAILABILITY.md` first — coverage
tables, the index-only rationale, the 2023-seam finding, and the PC gap record.

## One-line verdict
**INDEX-ONLY** catalog of **421 bundled whole-meeting packet/agenda PDFs, 2020 →
2026-07-16, 9.39 GB total** (Council + Committee of the Whole 232 · Planning
Commission 186 · other bodies 3). No PDFs on disk (`format=na`, `stored_locally=no`);
every row has a live `source_url` + exact `content_length_bytes`/`size_mb`. Notably,
**2023 council packets survive on CivicPlus even though 2023 council minutes were lost
to Tyler TMM** — 23 meeting dates, 18 of them minute-less.

## Sources & method
- **Council (+ CoW, School Coordinating Council, MCCD):** CivicPlus Archive Center
  listing `https://www.murray.utah.gov/Archive.aspx?AMID=83` ("City Council Agenda
  Packet"). One unpaginated HTML page lists all 290 items (2018→2026) as
  `Archive.aspx?ADID=<n>` links; the direct PDF is
  `https://www.murray.utah.gov/Archive/ViewFile/Item/<ADID>`. Titles carry the meeting
  date ("July 7, 2026 Council Meeting Packet").
- **Planning Commission:** two sources merged —
  1. Archive Center `Archive.aspx?AMID=32` (agendas + packets, 2009→early-2025; the
     2020–2022 era has BOTH a thin agenda row and a full packet row per meeting);
  2. DocumentCenter "Agenda & Packet" PDFs
     (`https://www.murray.utah.gov/DocumentCenter/View/<id>`), harvested from the
     rotating page `/779/Agendas-Attachment`, covering 2024-08 → present.
  For 9 dates present in both, the Archive Center row was kept (byte-identity
  spot-verified; the DocumentCenter copy is the same file).
- All requests GET-only, throttled ≥1.1 s/host, browser UA. Probe log:
  `raw/_fetch_log.jsonl`.

## index.csv
SCHEMA_SPEC §9 packets contract header, then Murray extras:
`date,title,body,meeting_type,packet_kind,source_url,retrieved_date,format,
extraction_method,path,adid,content_length_bytes,size_mb,stored_locally`
- `path` blank on every row (index-only); `format=na`; `stored_locally=no`;
  `extraction_method` documents the on-demand recipe.
- `adid` = the CivicPlus Archive item id (blank for the 28 DocumentCenter rows).
- One row per **document**, not per meeting: multi-part packets (2020–21 "Part 1/2/3")
  and PC agenda+packet pairs are separate rows sharing a `date`.

## Classification rules (title-driven)
- `body`: `Council` (default; includes Committee of the Whole rows) ·
  `PlanningCommission` (all AMID=32 + /779 rows) · `SchoolCoordinatingCouncil` ·
  `MurrayCityCenterDistrict` (the last two are city filings inside AMID=83).
- `meeting_type`: `regular` | `committee_of_the_whole` | `special` | `workshop` |
  `public_hearing` | `canceled` (14 PC cancellation notices) | `training`.
- `packet_kind`: `full_packet` iff the title says Packet (339 rows), else
  `agenda_packet` (thin agendas + notices, 82 rows). Two documented substance-over-title
  overrides to `full_packet`: "January 21, 2020 … Agenda & Documents" (18.8 MB) and
  "April 6, 2023 Planning Commission Meeting and Agenda" (70 MB) — bundled packets in
  all but name.
- Date parsing: "Month D, YYYY" titles, plus the 2024 PC dotted era ("11.07.24" =
  MM.DD.YY) and one hand-fixed source typo ("Janauary 2, 2024" → 2024-01-02, ADID 7677).

## Linkage to the vote layer
Join on `date` + `body`: council packet rows ↔ `../meeting_minutes/all_votes.csv`
(body=Council; council meets Tuesday, CoW usually the same Tuesdays); PC rows ↔
`../planning_commission/all_votes.csv` (Thursday). Packets are **pre-meeting**
documents: they explain what was before the body (staff reports, fiscal notes, zoning
analysis) but contain **no votes/outcomes** — outcomes stay in the minutes layer.
For the 18 minute-less 2023 council dates the packet is the best surviving record of
the agenda + staff analysis (see AVAILABILITY §2023 seam).

## Reading a packet on demand
```
python3 /Users/tysonwelsh/civic-data/.claude/skills/expand-city-sources/scripts/polite_fetch.py \
  --out /tmp/murray_pkt "<source_url>"
pdftotext -layout /tmp/murray_pkt/<file>.pdf -
```
Packets are born-digital (verified samples extract cleanly); map/plat/site-plan exhibit
pages need vision/OCR. **Vendor quirk:** CivicPlus DocumentCenter answers **404 to
HEAD** but serves GET normally — don't trust HEAD-based liveness checks on
`DocumentCenter/View/...` URLs (the Archive Center `ViewFile/Item/...` URLs HEAD fine).

## Caveats
- Index-only is a **documented allowed exception** to raw retention (public,
  re-fetchable files; ~9.4 GB would be stored otherwise). Provenance =
  `raw/_fetch_log.jsonl` + this index.
- The `/779/Agendas-Attachment` page **rotates**; the DocumentCenter URLs it points to
  are stable, but future PC packets must be re-harvested from the page (or from
  AMID=32 if the city resumes filing there).
- PC packet gap mid-2023 → 2024-07 is a **publishing gap** (same seam that took the PC
  minutes); do not read missing rows as scraper misses.
- Text sidecars now exist for the **34 2023 Council/CoW packets only** (fetched + extracted
  2026-07-17, binaries discarded — see "Primary-document text layer" below); every other row is
  still text-less index-only.

## Primary-document text layer (§9 trailing columns) — 2023 council fetched 2026-07-17
The index gained the five standardized **§9 pilot columns** (`doc_class, fetch_status, sha256,
text_path, text_chars`, appended after `stored_locally`). The **34 2023 Council/CoW packets**
(23 dates, the lost-minutes-era set) were **fetched, hashed, text-extracted, and the binaries
DISCARDED** (the sanctioned §9 text-only exception): `fetch_status=ok`, `sha256` of the fetched
binary, `text_path` sidecar under `text/`, `text_chars`, `extraction_method=pdftotext -layout`
(all 34 born-digital, clean yields 9k–631k chars). **`doc_class` is BLANK on every row —
honest:** a Murray packet is a whole-meeting BUNDLE (agenda + many staff reports/exhibits under
one PDF), not a single classifiable primary document; the §9 taxonomy is per-document, so a
bundle is genuinely unclassifiable without section-cutting (no machine-readable TOC anchor was
present to gate a high-confidence cut — recorded as a future candidate). Sidecars live in
`packets/text/<date>_<body>_<meeting_type>_<adid>.txt`; fetch provenance in
`raw/_primarydocs_fetch_log.jsonl`. **The rest stays INDEX-ONLY** (all PC + 2020–2022 & 2024–2026
council, ~5.6 GB) — future-candidate list in `AVAILABILITY.md`.
Byte-identical pair: 2023-10-17 CoW (ADID 7633) and regular (7634) share one 94 MB combined
packet (same sha256) — both rows carry the (identical) sidecar honestly.
The 2023 council *minutes* were later PMN-recovered/promoted (2026-07-16); these packets add the
**pre-meeting staff analysis** the minutes never carried.
