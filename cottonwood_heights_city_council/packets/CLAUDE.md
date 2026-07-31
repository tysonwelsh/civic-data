# packets/ — agenda packets & staff reports (Cottonwood Heights)

Additive dataset built by the `expand-city-sources` skill (source #1). **Does not modify any
existing dataset.** Read `AVAILABILITY.md` first — the headline is a narrow-window portal limit.

## One-line verdict
Cottonwood Heights publishes a **Packet** document (bundled whole-meeting PDF) alongside each
meeting's Agenda and Minutes, but the **Packet column is a much shorter rolling window than the
Minutes column** — only **council 2025-08-19→2026-07-07** and **PC 2024-11-06→2026-07-01** are on
the live portal. Older packets (all of 2020–2024, incl. the 2020–2021 floor) are **GRAMA-only**
(an honest retention limit). The full available window is **STORED** on disk (**52 packets,
471.6 MB**, born-digital with text sidecars).

## Source & method
- **Portal:** Granicus / CivicPlus **CivicEngage Central**, `https://www.cottonwoodheights.utah.gov`.
  The edge **403s a bare UA and a bare browser UA** — fetches used `scripts/polite_fetch.py`
  (browser UA; the probe returned 200, so the base header set sufficed here — the recon's full
  `Accept`/`Accept-Language`/`Sec-Fetch-Mode` set is the fallback if it 403s). GET-only, throttled.
- **Discovery:** two landing pages render a data **table** in the served HTML (not JS-only) with
  one row per meeting date and labeled anchors `Agenda | Packet | Minutes` (plus `Amended Agenda`,
  `Cancelled`, `Notice of Cancellation`, occasional case-numbered supplemental memos). Only the
  **`Packet`**-labeled `showpublisheddocument/<docId>/<versionToken>` anchor is harvested.
- **Same-day disambiguation:** the PC page lists **two meeting types on some dates** —
  `Planning Commission` (regular) and `Administrative Hearing` — each with its own Packet. These
  are kept as separate rows via `meeting_type` (`regular` vs `admin_hearing`).
- **Mode = STORED.** All 52 packets sized via HEAD (`polite_fetch.py --size-only`) → 471.6 MB,
  under the ~1.5 GB budget → downloaded verbatim to `raw/<date>/<docId>_<body>_<mtype>.pdf`.
- **Text sidecars:** `python3 scripts/extract_packet_text.py cottonwood_heights` →
  `text/<stem>.txt` for all 52 (`pdftotext -layout`; all born-digital, status `extracted`,
  log in `text/_extraction_log.csv`). These feed `cities.db` `fts_packet` on the next
  `build_cities_db.py` (NOT run here — orchestrator's step).

## Files
- `raw/<date>/` — 52 originals verbatim (~450 MB) + `_fetch_log.jsonl` per date (url, status,
  bytes, sha256, retrieved_utc).
- `text/<stem>.txt` — 52 born-digital text sidecars + `_extraction_log.csv`.
- `text/sections/<stem>__appxNN_<slug>.txt` — 17 land-use staff-report section cuts
  (primary-docs rollout, 2026-07-16) produced by `split_sections.py` (see "Section layer").
- `index.csv` — one row per packet (schema below).
- `AVAILABILITY.md` — the coverage window + GRAMA gap + size math + mode.
- Helper/build scripts (kept in-dataset, uniquely named per the concurrency rule):
  `parse_landing_ch.py` (landing-table → per-row anchors), `size_packets_ch.py` (HEAD sizing),
  `build_manifest_ch.py` (fetch manifest), `fetch_packets_ch.py` (download driver),
  `build_packets_index_ch.py` (index builder).

## index.csv schema (SCHEMA_SPEC §9 contract, exact prefix)
`date,title,body,meeting_type,packet_kind,source_url,retrieved_date,format,extraction_method,path`
then CH extras `size_mb,stored_locally,docid`, then the primary-docs-rollout columns
`doc_class,fetch_status,sha256,text_path,text_chars,parent_path,appendix_no,case_key`
(added 2026-07-16; blank on the 52 container rows — see "Section layer" below).
- `body` ∈ `Council` / `PlanningCommission` (matches `all_votes.csv` body labels; CDRA rides
  inside the council packet — no separate CDRA row).
- `meeting_type` — `regular` (council Work Session + Business Meeting; PC regular) or
  `admin_hearing` (PC Administrative Hearing) — disambiguates same-day PC docs.
- `packet_kind` = `full_packet` (the 52 stored container packets) **or `packet_section`**
  (the 17 land-use staff-report cuts, additive).
- `format` = `text` (all born-digital); `extraction_method` = `pdftotext-layout`.
- `path` — dataset-relative **including `raw/`** (validator requirement); **blank on
  `packet_section` rows** (a section has no separate binary — its bytes live in the parent).
- `stored_locally` = `yes` (containers) / `no` (sections — the flag describes the BINARY,
  which for a section does not exist separately); `size_mb` = on-disk size (blank for
  sections); `docid` = CivicEngage doc id (sections inherit their parent's).

## Section layer (primary-documents rollout, 2026-07-16) — `packet_kind='packet_section'`
CH is a **Bucket-B SEPARABLE** city: the **12 council work-session packets 2025-08-19 →
2026-02-17** carry an explicit machine-readable appendix manifest —

    Appendix 3 - Staff Report/Planning Department Land Use Amendment and Rezone at 3425 E.

followed later in the SAME sidecar by an indented body divider cover-page (`  Appendix 3`).
`split_sections.py` parses the manifest, locates each appendix's body divider, and cuts the
text of each **in-scope (land-use)** appendix into `text/sections/<parent_stem>__appxNN_<slug>.txt`,
adding one additive `packet_kind='packet_section'` row per cut. **17 cuts** (16 `staff_report`
+ 1 `general_plan`); parents and raw PDFs untouched.

- **Boundary semantics.** Section N = text from its body divider `Appendix N` up to the NEXT
  **appendix** divider (exclusive). An appendix that bundles its own exhibits as nested
  `Attachment N` cover-pages (e.g. 10491's WUI report carries HB48 / Draft Ordinance / WUI Map)
  keeps those exhibits as CONTENT — only the final appendix falls through to the top-level
  ordinance-attachment zone / EOF. (This nested-attachment case was the one boundary bug found
  and fixed in whole-class verification; the fix keeps every cut byte-faithful to its parent.)
- **Scope = land-use only.** CH labels EVERY work-session item `Staff Report/<subject>`, so the
  label is a form artifact, not a land-use signal. `classify()` cuts a section only on a
  positive land-use signal (rezone / zoning / subdivision / WUI / accessory-structure / general
  plan / road-access / a `ZMA|ZTA|CUP|SUB|OAM` case key); general-government memos (personnel,
  tax, curfew, events, Action Items) are left **UNCUT** (blank `doc_class` = honestly
  unclassified, never force-bucketed). Yield skews small because CH council packets are mostly
  general-government; the recurring "General Plan Update" is the most consistent land-use item.
- **`doc_class`**: `staff_report` (land-use staff analyses) | `general_plan` (a draft GP element
  exhibit — 10581 A4 embeds the `DRAFT WATER USE & PRESERVATION ELEMENT`; its canonical class-3
  home is `housing_plans/`, flagged there as a candidate to capture the standalone draft element
  if the city published one — NOT duplicated into housing_plans this wave). No
  `development_agreement` in the appendix corpus.
- **New columns on section rows**: `doc_class`, `fetch_status` (`ok` = text cut ≥200 chars;
  `needs_ocr` = image-only section, no usable text layer, **no sidecar written** — currently
  none), `sha256` (**blank** on sections by design — a section has no separate binary; byte
  provenance lives in the parent `full_packet` row + `raw/<date>/_fetch_log.jsonl`),
  `text_path` (dataset-relative sidecar), `text_chars`, `parent_path` (the parent packet's
  `raw/…pdf`), `appendix_no`, `case_key` (extracted `ZMA/CUP/…` where present).
- **NOT section-cut (honest):** the **32 PC packets** and the **8 newer council packets
  (2026-03-03 → 2026-07-07)** have no appendix manifest — PC packets open with the agenda and
  carry inconsistent (0–4) `STAFF REPORT` banners; the 2026-03+ council packets use an
  agenda-outline (`4.0 STAFF REPORTS / 4a./4b.`) structure. Their boundaries are not separable
  at high confidence, so they are left as full-packet text (their existing sidecars already
  serve `fts_packet`). **The appendix-TOC manifest exists only 2025-08 → 2026-02 (council).**
- **Skips:** `10625` Appendix 6 (Legislative Priorities) is listed in the TOC but has no body
  divider (dividers jump 5→7) → boundary unlocatable → skipped + logged (out of scope anyway).
- **Rerun (idempotent):** `python3 split_sections.py` (dry-run, read-only, prints the cut plan)
  · `python3 split_sections.py --write` (regenerates section rows + sidecars; drops any prior
  `packet_section` rows first, so re-running never duplicates).
- **Gate results (whole-class, n=17, 2026-07-16):** all 10 parent sidecars proven byte-identical
  to a fresh `pdftotext -layout` of their raw PDF; every one of the 17 cuts verified — starts at
  its own divider, subject matches the TOC title, ends exactly at the next appendix divider
  (no bleed; e.g. 10205 A3 rezone tail is RM-zone text, zero "Employee Handbook"; 10491 A3 WUI
  tail has zero "Chicken"), section file == parent line-range, `text_chars` exact. `doc_class`
  precision 17/17 land-use. `validate_dataset.py` PASS.
- **Acceptance candidate (Sharkey pattern):** `10205_council_regular__appx03_…rezone-.txt`
  (2025-08-19 council packet, Appendix 3, `doc_class=staff_report`, `case_key=ZMA-25-003`).
  Distinctive verbatim: *"The applicant is proposing to amend the General Plan land use map from
  Neighborhood Commercial to Residential Medium Density, and to subsequently rezone the property
  from Neighborhood Commercial (NC) to Residential Multifamily (RM) to subdivide and construct
  six townhomes."* The matter (3425 E. Bengal Blvd) was formally APPROVED by council as
  **Ordinance 452** on **2025-11-18** (`meeting_minutes/all_votes.csv`, motion_no 8, passed
  unanimously 5-0) — the staff analysis precedes the vote, exactly the primary-doc→vote link.

## Linkage to votes
Join `date` (+ `body`, `meeting_type`) to `meeting_minutes/all_votes.csv` (Council/CDRA) and
`planning_commission/all_votes.csv` (PC). **18/20** council packet dates and **13/25** PC packet
dates match an existing vote date; the rest are Administrative Hearings (no roll call) or dates
that post-date the current vote extraction (a future refresh will absorb them). See
`AVAILABILITY.md` "Join coverage".

## Refresh
Re-fetch the two landing pages, re-run `parse_landing_ch.py` → `build_manifest_ch.py` (re-sizes)
→ `fetch_packets_ch.py` (idempotent; skips existing) → `build_packets_index_ch.py` →
`scripts/extract_packet_text.py cottonwood_heights`. Because the portal is a **rolling window**,
periodic capture is the only way to accumulate a packet history — packets older than the current
window rotate off permanently (GRAMA-only thereafter).

## Validate
`python3 .claude/skills/expand-city-sources/scripts/validate_dataset.py cottonwood_heights_city_council/packets`
→ **PASS**.
