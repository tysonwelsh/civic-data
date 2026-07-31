# packets/ — agenda packets & staff reports (Bluffdale)

Additive dataset built by the `expand-city-sources` skill (source #1). **Does not
modify any existing dataset.** Read `AVAILABILITY.md` first — it has the coverage
table, the index-only rationale, and the "is there a packet doc-type?" answer.

## One-line verdict
Bluffdale posts a **genuine full staff-report PACKET for every regular Council and
Planning Commission meeting, 2020→present** (217 packets, 2.85 GB). Built
**INDEX-ONLY** (`format=na`, `stored_locally=no`, live `source_url` + exact
`size_mb`) — the bundled whole-meeting PDFs are too large to store for one city.

## Source & method
- **Portal:** CivicPlus / CivicEngage Central AgendaCenter, `https://www.bluffdale.gov`.
  No bot-block; every request went through `scripts/polite_fetch.py` (browser UA,
  GET-only, throttled).
- **Enumeration:** the Search endpoint
  `https://www.bluffdale.gov/AgendaCenter/Search/?CIDs=<CID>%2C&startDate=MM%2FDD%2FYYYY&endDate=MM%2FDD%2FYYYY&term=&dateRange=&dateSelector=`
  — **CID=2 = City Council, CID=3 = Planning Commission** — fetched one year at a
  time, 2020–2026, for both bodies. Each `catAgendaRow` block was parsed for its
  `ViewFile/Agenda/_<MMDDYYYY>-<id>` link + anchor-text title + presence of a
  Minutes link. Internal ids are **not derivable** — harvested from the labeled
  `<a>` links, never guessed.
- **Doc-type discovery:** the `ViewFile` endpoint exposes only **`Agenda`** and
  **`Minutes`** types — **no distinct packet doc-type** and no DocumentCenter
  "Agenda Packets" area. Bluffdale uploads the full packet **as an extra
  `Agenda`-type document**, identified by **"PACKET"/"Packet"** in its title. So
  each regular meeting has a thin agenda (with the Minutes link) AND a separate
  full PACKET. This dataset indexes the **PACKET rows only**.
- **Classification:** a row is a `full_packet` iff its title contains
  "PACKET"/"Packet"; all other `Agenda`-type rows (thin agendas, public-hearing /
  budget / text-amendment notices, election notices, cancellations, canvasser
  reports, quorum notices) were excluded. `meeting_type` derived from the title
  (work_session / special / else regular).
- **Sizing:** all 217 packet URLs were **HEAD-probed** with
  `polite_fetch.py --size-only` on 2026-07-13 (0 failures) to record exact
  `content_length_bytes`/`size_mb` and confirm liveness. Sample bodies were
  GET-verified as real packets (e.g. the 2026-01-28 Council packet = 71 pp:
  agenda + staff reports, born-digital text).

## Why INDEX-ONLY
217 packets total **2.85 GB** (median 6.1 MB, max 144 MB) — bundled whole-meeting
PDFs heavy with maps/plats/site-plans. Storing them for one city exceeds a
reasonable disk budget, so per the skill's documented allowed exception the
dataset is index-only: no PDFs on disk, `format=na`, `stored_locally=no`, a live
`source_url` + `size_mb` per row, and HEAD-probe provenance in
`raw/_fetch_log.jsonl`. The files are public and re-fetchable. Same mode as South
Jordan and Vineyard packets.

## Reading a packet on demand
```
python3 scripts/polite_fetch.py "<source_url>" --out /tmp/x --name packet.pdf
pdftotext -layout /tmp/x/packet.pdf -      # born-digital staff-report text
# large map/plat-heavy packets: read exhibit pages with the Read tool / OCR
```

## Files
- `index.csv` — 217 rows, one per full packet. §9 packets contract header
  (`date,title,body,meeting_type,packet_kind,source_url,retrieved_date,format,
  extraction_method,path`) + city extras
  (`agenda_internal_id,content_length_bytes,size_mb,stored_locally`). `path` is
  empty (index-only); `body` ∈ `Council` / `PlanningCommission`; keyed by
  `date` + `body` (+ `meeting_type`). Titles are **verbatim** (source typos and
  `*Amended*` markers preserved).
- `raw/_fetch_log.jsonl` — HEAD size-only probe record for all 217 URLs
  (url, bytes, `"probe":"HEAD size-only"`, retrieved_utc). No PDFs stored.
- `AVAILABILITY.md` — coverage table, asymmetry note, gap record.

## Linkage
Join to the vote/minutes layer on `date` + `body`: a Council packet row joins to
`meeting_minutes/all_votes.csv` rows for that date (which include the in-session
RDA/LBA motions bundled in the same packet); a PlanningCommission packet joins to
`planning_commission/all_votes.csv`. The packet is the *why* behind each item's
staff recommendation and the PC→Council referral.

## Caveats
- **Not stored** — you must fetch to read; see above.
- **No council/PC publishing asymmetry** — both bodies publish a full packet per
  regular meeting across 2020→2026 (Council 132 / PC 85; the difference is meeting
  cadence, not coverage).
- Older 2020 packets use the title form "…Agenda and Packet"; 2021+ use "…PACKET".
  Both are captured.
- Do NOT run `scripts/build_cities_db.py` from here — the federation orchestrator
  loads this `index.csv` into the `document` catalog once at the end. (Index-only
  rows have `format=na`, so there is no `fts_packet` text to index for Bluffdale.)

## Primary-document classes / text layer
Assessed 2026-07-16 (doc_class rollout) — **not separable without fetch**. On **2026-07-17
(wave-2)** a bounded **60-packet** high-value set (contested + land-use meeting dates,
contested-first, ≤40 MB) was fetched, `pdftotext`-extracted to `text/<slug>.txt`, and the
binaries discarded (the §9 text-only-corpus exception). The five §9 pilot columns
(`doc_class,fetch_status,sha256,text_path,text_chars`) are now populated on those 60 rows
(`fetch_status=ok`, all born-digital); the remaining 157 rows stay index-only. **`doc_class`
is BLANK on all 60** — a whole-meeting bundle maps to no single §9 class at ≥95% precision, and
no rigid TOC anchor exists to section-cut on (honest default), so the whole-packet sidecar is
the searchable artifact. One `-layout` whitespace-blowup (2020-01-08 PC) was re-extracted with
plain `pdftotext` (`pdftotext_raw`). Provenance: `raw/_targeted_fetch_log.jsonl`. See
`AVAILABILITY.md` § "Targeted text-layer fetch (2026-07-17, wave-2)".
