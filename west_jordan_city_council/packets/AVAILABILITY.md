# packets/ — availability & gap log (as-of 2026-07-03)

What was checked, what West Jordan publishes, and what it doesn't. Built by
`expand-city-sources` Source 1. Portal = **PrimeGov** (`westjordan.primegov.com`).

## Method (what was checked)
For every year **2020–2026**, the PrimeGov archive API
`GET /api/v2/PublicPortal/ListArchivedMeetings?year=YYYY` was pulled (7 JSON files,
`raw/api/`-equivalent captured in the build). Every meeting belonging to the
**council family** (City Council, Committee of the Whole, RDA, MBA — the bodies whose
votes live in `../meeting_minutes/all_votes.csv`, body ∈ Council/RDA/MBA) or the
**Planning Commission** was classified, and its `documentList` inspected for a packet
document (`templateName` ∈ Complete Packet / Meeting Materials / Packet /
RDA Meeting Materials / MBA Meeting Materials / Meeting Materials_Amended). Each packet's
download URL (`/Public/CompiledDocument?meetingTemplateId=<templateId>`) was
**stream-probed for Content-Length only** (headers read, body never downloaded) on
2026-07-03. All 222 probes returned HTTP 200 `application/pdf` (`raw/_fetch_log.jsonl`).

## What exists — 222 bundled packets, INDEX-ONLY
PrimeGov exposes **one bundled compiled packet PDF per meeting** (agenda + every staff
report + all exhibits), **not** separable per-item staff-report PDFs. They are large and
map/plat/site-plan-heavy: **min 0.4 MB, median 12.8 MB, max 330 MB; full 222-set = 7.36 GB.**
Not born-digital text — reading one needs **vision/OCR**, not `pdftotext`. Per the
disk-constrained Source-1 mode, **no PDFs are stored**; `index.csv` is a pointer table
(`source_url` re-resolves a fresh Azure SAS on each fetch). See `CLAUDE.md`.

| Year | Council | RDA | MBA | Planning Commission |
|------|--------:|----:|----:|--------------------:|
| 2022 | 25 | 2 | 0 | 10 |
| 2023 | 38 | 7 | 3 | 19 |
| 2024 | 40 | 8 | 4 | 20 |
| 2025 | 19 | 4 | 2 | 20 |
| 2026 | 0 | 0 | 0 | 1 |
| **Total** | **122** | **21** | **9** | **70** |

## Coverage vs recorded votes (the join)
Packet date = meeting date; it matches the vote date **exactly** (no off-by-one — verified
for all 2023–24 dates). Council-family votes are in `../meeting_minutes/all_votes.csv`
(body Council/RDA/MBA); PC votes in `../planning_commission/all_votes.csv`.

**Council vote-date coverage by year:** 2020 0/27 · 2021 0/23 · 2022 12/23 · **2023 25/25**
· **2024 23/23** · 2025 8/22 · 2026 0/10.
**Planning Commission:** **2022 6/6 · 2023 13/13 · 2024 15/15 · 2025 12/12** · 2026 0/3.

→ **2023 and 2024 have 100% packet coverage for both bodies.** The gaps below are real
West Jordan publishing patterns, not scraper misses.

## Gaps (verified, with cause)

1. **2020–2021: no packets published (publishing gap).** These meetings carry only
   `Agenda` + `HTML Agenda` + `Minutes` in PrimeGov — no packet document of any template
   exists. (76 council-family meetings, agenda+minutes only.) PrimeGov packet publication
   for West Jordan began in **2022** (and ramped up through mid-2022 — 17 council-family +
   1 PC meeting in early 2022 are still agenda-only).

2. **Mid-2025 onward — format shift to in-portal "HTML Interactive Agenda."** Starting
   mid-2025 West Jordan stopped compiling a downloadable packet PDF and moved to an
   **HTML Interactive Agenda** (`compileOutputType=3`, `templateName "HTML Interactive
   Agenda"`) rendered client-side in the PrimeGov portal SPA. **72 council-family meetings**
   (29 council 2025, 28 council 2026, plus 2025–26 RDA/MBA) have an interactive agenda but
   **no downloadable compiled packet**. The per-item attachments are viewable only through
   the portal viewer; `/Public/CompiledDocument?meetingTemplateId=<interactive-agenda-id>`
   returns `PublishedDocumentError`, and no stable per-meeting/per-item attachment URL or
   JSON endpoint was found (the portal is a compiled SPA; `GetMeeting*` API routes 404).
   These meetings are therefore **not indexable as fetchable packets** and are recorded here
   as a documented format-shift gap, not as index rows. (2025 PC still published a
   Complete Packet PDF — 20 of them — so PC 2025 is fully covered; PC 2026 reverted to
   agenda+minutes only for its 3 dates.)

3. **2026 Planning Commission: agenda+minutes only** — 13 PC meetings in 2026 carry no
   packet and no interactive agenda (only `Agenda`+`Minutes`). Only the one 2026-01-27 PC
   meeting had a Complete Packet.

## Not applicable / not done
- **Separable small staff-report downloads:** not possible — West Jordan bundles the whole
  meeting into one compiled PDF; there is no per-agenda-item PDF to download small. So the
  skill's "download the small reports, cap the exhibits" branch does not apply here; the
  bundled-PDF INDEX-ONLY branch does.
- **RDA/MBA included** (body-labeled) because the council sits as those bodies and their
  votes are in `../meeting_minutes/all_votes.csv`; a consumer scoped strictly to "council"
  can filter `body=Council`.

## Regenerate / refresh
Re-pull `ListArchivedMeetings?year=YYYY` for each year, re-classify council-family + PC
meetings, find each meeting's packet document, and re-probe
`/Public/CompiledDocument?meetingTemplateId=<templateId>` for Content-Length. Watch for the
interactive-agenda format: if West Jordan later exposes a compiled-packet or per-item
attachment endpoint for those meetings, backfill 2025 H2–2026.

## Primary-document classes (doc_class rollout, 2026-07-16)

**Ruling: honest no — non-separable portal.** Under the repo-wide primary-documents rollout
(`PRIMARY_DOCS_ROLLOUT.md`, triage 2026-07-16) West Jordan was bucketed **B-no**. All
**222 packets are INDEX-ONLY compiled bundles** (7.36 GB, median 12.8 MB, max 330 MB); as
documented above, **PrimeGov exposes no separable per-agenda-item staff-report PDFs** — one
compiled whole-meeting PDF per meeting, image/map-heavy (vision/OCR to read). The four
attachment-borne classes — `staff_report`, `member_memo`, `plan_amendment`,
`development_agreement` — cannot be broken out. The **mid-2025+ "HTML Interactive Agenda"
(SPA) era has no downloadable packet at all** (the existing known format-shift gap, §2
above), so there is nothing to classify there either. Nothing is fetched, classified, or
section-cut in this rollout; no `doc_class`/`text_path` column is added. Class 3
(`general_plan`) lives in `housing_plans/`.
