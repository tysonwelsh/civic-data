# packets/ — availability & gap log (as-of 2026-07-03)

What was checked, what Provo publishes, and what it doesn't. Built by `expand-city-sources`
Source 1. **Two portals:** council packets on Hyland **OnBase** (`agendas.provo.gov`,
documentType=5); Planning Commission packets on CivicPlus **AgendaCenter**
(`www.provo.gov/AgendaCenter`, `ViewFile/Agenda/<ref>`). See `CLAUDE.md` for the full access
method (OnBase CSRF token + session cookie + `DownloadFileBytes`; AgendaCenter PC-section
enumeration).

## Method (what was checked)
- **Council:** the OnBase POST `/Meetings` search (DateRangeOptionID=11) was run live for
  2022–2025 to confirm the portal's body set — it returns **Municipal Council only** (Council
  Meeting, Work Meeting, budget/priorities retreats, Truth-in-Taxation, Board of Canvassers,
  joint meetings). No standalone Planning Commission / RDA / Stormwater meetings exist in this
  portal (PC appears only as council "Joint Meeting with Planning Commission"). The council
  packet rows are derived from `../meeting_minutes/minutes_index.csv` `packet_url`
  (documentType=5, `DownloadFileBytes` URL), which the repo's `../fetch_new.py` OnBase session
  pipeline already populates for every council meeting 2020–2026. GET liveness spot-checked
  across years (200 `%PDF`).
- **Planning Commission:** the CivicPlus AgendaCenter search was pulled per year 2022–2026;
  the `<h2>Planning Commission</h2>` section (excluding "Planning Commission Administrative
  Hearings") yielded 85 `ViewFile/Agenda/<ref>` packet URLs, each **HEAD-probed for
  Content-Length** on 2026-07-03 (all 200 `application/pdf`, logged in `raw/_fetch_log.jsonl`).

## What exists — 391 bundled packets, INDEX-ONLY
Both portals expose **one bundled compiled packet PDF per meeting** (agenda + staff reports +
exhibits), **not** separable per-agenda-item staff-report PDFs. Council packets are large and
map/plat/site-plan-heavy; PC packets from mid-2025 likewise. Not born-digital text — reading
one needs **vision/OCR**, not `pdftotext`. Per the disk-constrained Source-1 mode, **no PDFs
are stored**; `index.csv` is a pointer table.

| Year | Council packets | PC packets (full / thin) |
|------|----------------:|-------------------------:|
| 2020 | 51 | — |
| 2021 | 51 | — |
| 2022 | 50 | 19 (0 / 19) |
| 2023 | 45 | 16 (0 / 16) |
| 2024 | 49 | 18 (0 / 18) |
| 2025 | 42 | 20 (16 / 4) |
| 2026 | 18 | 12 (10 / 2) |
| **Total** | **306** | **85 (26 / 59)** |

"full" = `full_packet` (staff-report bundle, multi-MB); "thin" = `agenda_packet` (~100 KB
agenda outline only, no staff reports).

## Size math
- **Council: sizes unobtainable cheaply.** OnBase serves `Transfer-Encoding: chunked` with
  **no `Content-Length`** on HEAD *or* streaming GET, so a packet's size can't be read without
  a full download — which this run deliberately avoids (`--size-only` returns null here). Real
  sizes exist for the **26** council packets already on disk from the `public_comments`
  harvest (measured from disk, no new fetch): **min 18.2 MB · median 36.7 MB · mean 51.9 MB ·
  max 148.2 MB.** Extrapolated, the full **306-packet council set ≈ 16 GB** — the reason
  index-only is the correct mode here.
- **PC: fully measured.** All 85 PC packets carry a real HEAD `Content-Length`; total =
  **142.6 MB** (2022–24 thin outlines ≈ 6.8 MB; 2025–26 full packets ≈ 135 MB).

## Coverage vs recorded votes (the join)
Packet date = meeting date, exact match. **100% of recorded vote dates have a packet, both
bodies:**
- **Council: 147/147** vote dates covered — 2020 26/26 · 2021 24/24 · 2022 25/25 · 2023 23/23
  · 2024 22/22 · 2025 19/19 · 2026 8/8. (Council votes in `../meeting_minutes/all_votes.csv`.)
- **Planning Commission: 26/26** vote dates covered — 2025 16/16 · 2026 10/10. (PC votes in
  `../planning_commission/all_votes.csv`; the PC record is 2025+ only.)

## Gaps (verified, with cause)
1. **5 council meetings have no docType=5 packet** (agenda + minutes only, no packet
   published): 2021-04-13 Work Session, 2023-09-26 Joint Meeting w/ School District,
   2025-01-07 Budget Priorities, 2025-10-07 Council Regular, 2026-05-05 Council Meeting
   (Tentative Budget). **None is a recorded vote date**, so vote-date coverage stays 100%. A
   publishing gap, not a scraper miss.
2. **2022–2024 PC packets are thin agenda outlines (~100 KB), not full staff-report bundles**
   (59 of 85 PC rows, `packet_kind=agenda_packet`). Provo's CivicPlus PC packets only became
   full staff-report bundles in **mid-2025** — exactly when standalone PC **minutes** first
   appear in this repo (the PC record is 2025+; `../planning_commission/minutes_unrecovered.csv`
   documents the 2020–2024 PC minutes source gap). So for 2022–24 the PC "packet" gives the
   agenda/item list but not the staff analysis. These are still indexed (they scope the items)
   and flagged by `packet_kind`.
3. **No standalone PC / RDA / Stormwater packets on OnBase.** `agendas.provo.gov` is
   council-only; those bodies are not published there. PC is covered via AgendaCenter above;
   RDA/Stormwater packets were not located on either portal and are out of scope for this
   council+PC dataset.

## Not applicable / not done
- **Separable small staff-report downloads:** not possible — both portals bundle the whole
  meeting into one compiled PDF; there is no per-agenda-item PDF to download small. The
  skill's "download the small reports, cap the exhibits" branch does not apply; the
  bundled-PDF INDEX-ONLY branch does.
- **`polite_fetch.py --size-only` for council:** returns null (OnBase chunked, no
  Content-Length) — documented above, not a tool failure.
- **No packet body was downloaded** in this Source-1 run; the 26 council sizes reuse PDFs
  already on disk from the earlier `public_comments` build.

## Regenerate / refresh
See `CLAUDE.md` § Regenerate. Council: re-derive from `minutes_index.csv` `packet_url` or
re-scrape OnBase (session cookie + `DownloadFileBytes`). PC: re-enumerate the AgendaCenter
"Planning Commission" section per year and HEAD-size each `ViewFile/Agenda/<ref>`.

## Primary-document classes (doc_class rollout, 2026-07-16)

**Ruling: honest no — classes not separable across either portal.** Under the repo-wide
primary-documents rollout (`PRIMARY_DOCS_ROLLOUT.md`, triage 2026-07-16) Provo was bucketed
**B-no**. All **391 packets are INDEX-ONLY bundles across two portals**, with no
per-attachment rows or matter metadata:

- **Council (OnBase, 306):** session-gated (CSRF + cookie) and served **chunked with no
  `Content-Length`** — sizes are largely unknown and a fetch requires the OnBase session
  (≈16 GB extrapolated). One compiled whole-meeting PDF per meeting, image/map-heavy.
- **PC (CivicPlus, 85):** the **2022–2024 rows are thin agenda outlines** (~100 KB, no
  staff analysis); full staff-report packets exist **2025+ only**.

So the four attachment-borne classes — `staff_report`, `member_memo`, `plan_amendment`,
`development_agreement` — cannot be separated. Nothing is fetched, classified, or
section-cut in this rollout; no `doc_class`/`text_path` column is added. Class 3
(`general_plan`) is handled in `housing_plans/`.
