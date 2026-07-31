# packets/ — South Salt Lake agenda packets (INDEX-ONLY)

Additive `expand-city-sources` dataset (source type 1). **Read `AVAILABILITY.md` first** for
coverage, the size math, and the stored-vs-index decision. This file documents the *build*.

## What this is
A catalog of **429 agenda packets** from the SSL CivicPlus AgendaCenter for four bodies —
City Council (`cat4`), Planning Commission (`cat3`), Redevelopment Agency (`cat5`), Civilian
Review Board (`cat2`) — 2020–2026. The AgendaCenter "Agenda" **and** "Minutes" slots both
serve the *agenda packet* (agenda + staff reports + attachments); the recorded roll-call
**minutes** are on PMN and belong to the core `meeting_minutes/`+`planning_commission/`
layers, NOT here. So this dataset is the staff-analysis / "why" layer that joins to the
minutes/votes by meeting **date + body + meeting_type**.

**INDEX-ONLY:** no PDFs on disk (3.37 GB total > budget; PC packets are bulky image/map
PDFs). Each row is a live `source_url` + HEAD-probed size. `format=na`,
`stored_locally=no`, `extraction_method=not_retrieved`.

> **Primary-document classes (doc_class rollout, 2026-07-16): honest no (row-level).** The
> four attachment-borne classes (`staff_report`/`member_memo`/`plan_amendment`/
> `development_agreement`) are **not separable** — 429 assembled INDEX-ONLY bundles, no
> per-attachment rows or matter metadata. See `AVAILABILITY.md` § Primary-document classes.
>
> **UPDATE 2026-07-17 — targeted TEXT fetch of 72 high-value packets.** The future-fetch
> candidate was executed for a bounded subset: the packets tied to **contested votes** and
> **land-use items** (derived read-only from `db/civic.db`; Council 28 / PC 39 / RDA 5),
> capped ≤35 MB/item. All 72 are born-digital → `pdftotext` sidecars under `text/`, binaries
> discarded (sanctioned exception; `sha256` + `raw/_targeted_fetch_log.jsonl` provenance
> retained). Standardized pilot trailing cols added to `index.csv`
> (`doc_class,fetch_status,sha256,text_path,text_chars`). **`doc_class` stays BLANK** on all
> 72 — full_packet bundles are not one class and carry no section-cut anchor (honest "not
> separable"). The other 357 rows remain index-only. See `AVAILABILITY.md`.

## index.csv schema
SCHEMA_SPEC §9 packets contract header (exact, enforced by `validate_dataset.py`):
```
date,title,body,meeting_type,packet_kind,source_url,retrieved_date,format,extraction_method,path
```
then city extras (after the contract cols, St. George index-only convention):
```
content_length_bytes,size_mb,stored_locally,cancelled
```
- `body` ∈ Council | PC | RDA | CRB (classified from the AgendaCenter category).
- `meeting_type` ∈ regular | work | special (parsed from the item title; SSL Council days
  carry a 6:30 pm **work** + 7:00 pm **regular** meeting as two items).
- `packet_kind` = `full_packet` for every row — `source_url` is the `?packet=true`
  assembled-packet endpoint (see below).
- `source_url` = `…/AgendaCenter/ViewFile/Agenda/_MMDDYYYY-<id>?packet=true`.
- `cancelled=yes` marks a posted-then-cancelled meeting (kept as an honest row).
- `path` is blank (index-only). If a packet is ever retrieved, set `path=raw/<date>/<file>`
  (dataset-relative **including `raw/`**), `stored_locally=yes`, `format`, `extraction_method`.

## The `?packet=true` finding (key vendor quirk)
CivicPlus exposes several agenda-slot variants per item: the plain `/ViewFile/Agenda/_<id>`,
`?html=true` (HTML view), and `?packet=true` (the assembled full packet). The plain slot is
sometimes only a thin agenda **outline** (PC 2022-01-20 plain = 2.9 KB) while `?packet=true`
is the full packet (same item = 4.1 MB). For most items the uploaded agenda already *is* the
packet, so plain == `?packet=true`; `?packet=true` is `>=` plain in every case checked, so it
is the safe universal choice and is what every `source_url` uses.

## Build (reproduce)
All scripts live here (unique `_ssl` names) and are idempotent:
1. **Enumerate** — fetch each category-year listing (browser UA), 4 cats × 2020–2026, into
   `raw/_listings/cat<c>_<yr>.html` via the AJAX endpoint
   `UpdateCategoryList?catID=<c>&year=<YYYY>&term=&Keywords=`.
2. `python3 build_packets_index_ssl.py` — parse each `catAgendaRow`: item id (`MMDDYYYY-<seq>`),
   date, best (most descriptive) anchor title, meeting_type, whether a Minutes-slot link is
   also present → `raw/_catalog.tsv`.
3. `python3 size_packets_ssl.py` — HEAD-probe every item's `?packet=true` URL for
   `Content-Length` (no body GET; polite ≥1s/host), logging each probe to
   `raw/_fetch_log.jsonl` → `raw/_sizes.tsv`. (Use a `(connect,read)` timeout tuple, e.g.
   `(10,15)` — a few RDA `?packet=true` HEADs stall on a bare 30 s single-value timeout.)
4. `python3 build_final_index_ssl.py` — join catalog + sizes → `index.csv`, and print the
   coverage/size report.
5. `python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .` → PASS.

## Provenance (retained in raw/)
- `raw/_fetch_log.jsonl` — one JSONL line per HEAD size-probe (url, status, bytes, utc). 429
  packet-URL probes, all HTTP 200.
- `raw/_listings/` — the 28 AgendaCenter category-year listing HTML pages (discovery source).
- `raw/_catalog.tsv`, `raw/_sizes.tsv` — intermediate build artifacts.
No packet PDFs are retained (index-only, documented exception — `AVAILABILITY.md`).

## Linkage to the rest of the repo
Join a packet to `meeting_minutes/all_votes.csv` / `planning_commission/all_votes.csv` /
minutes markdown by **date + body (+ meeting_type)**. Council packets pair with the Council/RDA
minutes; PC packets with the PC minutes. Because SSL's recorded minutes have a coverage cliff
(see the city `README.md`/`COVERAGE.md`), a packet often exists for a meeting whose recorded
minutes do not — the packet is then the only staff-analysis record for that date.

## Caveats
- Not the recorded minutes; no votes here. Mayor is non-voting (strong-mayor form) — a packet
  linkage must not treat the Mayor as a councilmember.
- Index-only: reading a packet requires fetching it (vision/OCR for the map/plat-heavy ones).
- Cancelled meetings and tiny notice stubs are retained as honest rows (`cancelled=yes` /
  small `size_mb`), never dropped.
