# packets/ — agenda packets & staff reports (INDEX-ONLY) — as-of 2026-07-13

Built by `expand-city-sources` (Source 1). The staff analysis (fiscal notes, zoning
analysis, alternatives, staff recommendation) behind each Herriman **City Council**,
**Planning Commission**, **CDRA**, **HCSEA**, **HCFSA**, and **Joint CC/PC** agenda item —
the "why" behind a motion in `../meeting_minutes/all_votes.csv` (body Council/CDRA/
HCSEA/HCFSA) and `../planning_commission/all_votes.csv`.

> **Primary-document classes (doc_class rollout, 2026-07-16): honest no.** The four
> attachment-borne classes (`staff_report`/`member_memo`/`plan_amendment`/
> `development_agreement`) are **not separable for this PrimeGov portal** — 372 whole-meeting
> INDEX-ONLY bundles, no per-item docs or matter metadata, image/map-heavy. Nothing
> fetched/classified/section-cut. See `AVAILABILITY.md` § Primary-document classes.

## Two sources, one index

1. **PrimeGov (2021 → present), 340 rows.** Same vendor + document model as West Jordan:
   `ListArchivedMeetings?year=YYYY` → per-meeting `documentList[]`; the packet is the
   entry with `templateName == "Packet"` — **one bundled compiled whole-meeting PDF**
   (agenda + all staff reports + all exhibits); PrimeGov exposes no separable per-item
   staff-report PDFs. Download (stable):
   ```
   GET https://herriman.primegov.com/Public/CompiledDocument?meetingTemplateId=<templateId>
   ```
   (`templateId`, NOT the doc `id` / meetingId). It 302-redirects to a **time-limited**
   Azure blob (`pgwest.blob.core.windows.net/herriman/...?<SAS>`, ~2-day expiry) — always
   fetch via the `CompiledDocument` URL, never cache a blob URL. Browser UA required.
2. **Legacy S3 bucket (2020 only), 32 rows.** PrimeGov has nothing before 2021-01-07; the
   pre-PrimeGov WordPress site's bucket still serves 2020 packets:
   `s3-us-west-1.amazonaws.com/herriman-agendas/2020-agendas/2020-city-council-packets/`
   and `.../2020-planning-commission-packets/`. Two key grammars
   (`YYYY_MM_DD[_SUFFIX].pdf` and `YYYY_MM_DD+[QUALIFIER+]Packet.pdf`) — the indexed
   `source_url` is the exact live key; don't template new ones. **Legacy host, could be
   retired at any time** (2020 partial by source — see `AVAILABILITY.md`).

## This is a LINK INDEX, not a document store — by deliberate design

The 372 packets total **11.43 GiB** (median 17.4 MB, max 297 MB) — ~7.6× the disk budget
— and are image/map/plat-heavy bundles (**not** reliably text-convertible; vision/OCR to
read one). Per the repo's budget rule (same call as West Jordan / bluffdale / murray),
**no packet PDF is stored locally**: `format=na`, `stored_locally=no`, empty `path`.
This is the documented, allowed exception to "retain every raw original" — the files are
public and re-fetchable; `raw/_fetch_log.jsonl` (435 records) retains the probe
provenance (every packet sized 2026-07-13 via 1-byte ranged GET on PrimeGov / HEAD on S3;
no body downloaded; negatives logged too).

## How an LLM/agent should use this

1. Find the meeting in `index.csv` by `date` + `body` (+ `meeting_type`; `title`
   disambiguates the few Part 1/Part 2 and Work Meeting 1/2 same-day pairs).
2. Check `size_mb` (some >100 MB), then **fetch `source_url`** (public GET, browser UA,
   follow the 302).
3. Extract with **vision or OCR**, not `pdftotext`. Label whatever you produce.
4. Bulk re-hydration: feed the `source_url` column to
   `.claude/skills/expand-city-sources/scripts/polite_fetch.py --batch` **without
   `--max-bytes`**. Budget ~11.5 GiB for all 372 (~1.7 GiB for 2020-S3 alone —
   mirror those first if preservation is the goal).

## index.csv columns

§9 contract: `date, title, body, meeting_type, packet_kind, source_url, retrieved_date,
format(=na), extraction_method(=not_retrieved), path(empty)`; extras:
`template_name, template_id, meeting_id, content_length_bytes, size_mb,
stored_locally(=no), probe_status`.

- `body` ∈ `Council` (190) / `PlanningCommission` (121) / `CDRA` (19) / `HCSEA` (18) /
  `HCFSA` (16) / `JointCCPC` (8). Council+CDRA+HCSEA+HCFSA votes live in
  `../meeting_minutes/all_votes.csv` (same `body` values, except JointCCPC which has no
  vote rows); PC votes in `../planning_commission/all_votes.csv`.
  Two HCFSA/HCSEA meetings filed under PrimeGov committeeId 3 were re-tagged by title.
- `meeting_type` ∈ `regular` / `work` / `special` (strategic-planning meetings → special;
  title keeps the verbatim name).
- `packet_kind` = `full_packet` for all 372 (every packet is the bundled whole-meeting
  compiled PDF; the one thin `HTML Mini-Packet` template is dead at source and excluded —
  see `AVAILABILITY.md`).
- `template_name`/`template_id`/`meeting_id` are PrimeGov-only (blank on the 32 S3 rows).
- `probe_status`: `206` = PrimeGov ranged-GET probe OK; `200` = S3 HEAD probe OK.
- S3-row `title` is derived (minutes-index title where the date matches, else the
  Wayback anchor text / folder name — e.g. "Joint Work Meeting", "HCSEA Meeting");
  PrimeGov titles are verbatim API strings.

## Join notes

- 2021+ coverage of recorded-vote dates is near-total (100% for 2021/2023/2024/2026
  council; see `AVAILABILITY.md` table). Packet date == meeting date, no offset.
- Six 2020 packets exist for dates with **no minutes in the repo** (2020-05-13, 07-29,
  09-23, 11-05, 12-09; PC 2020-12-03) — evidence a meeting was scheduled; do not invent
  vote rows for them.
- The council packet for a combined work+general Wednesday is a single document, matching
  the combined minutes doc.

## Regenerate / refresh

Re-pull `ListArchivedMeetings?year=YYYY` for 2021→current (browser UA), keep committeeIds
{3, 4, 8, 9, 12, 14}, classify body/meeting_type from committeeId + title (HCFSA/HCSEA
title override under committee 3; skip cancelled/ceremonial/canvass rows without packets),
take each meeting's `Packet` templateId, size via ranged GET (HEAD is broken on this
host), and rebuild the PrimeGov rows; the 32 S3 rows are static history (re-HEAD them to
confirm the bucket still serves). Keep the exclusion rule: only probe-OK URLs get rows.
