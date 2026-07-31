# PRIMARY_DOCS_ROLLOUT — classes 1–5 for the remaining 30 cities

> **✅ EXECUTED + CLOSED 2026-07-16.** All 30 cities dispositioned per the triage table
> below; owner sign-off honored (order as proposed; section-cuts CH+magna only). Yields:
> 2,093 newly classified rows across 9 Bucket-A cities + 221 section-cut rows (CH 17,
> magna 204) + 19 honest completions + class-3 closures (WVC, st_george). One federation:
> integrity ok, reconciliation exact, fts_packet 12,660→12,930, all 11 Sharkey-pattern
> acceptance checks PASS (doc_class-filtered). Durable record: TODO.md primary-docs item;
> per-city detail in each packets/CLAUDE.md + AVAILABILITY.md; backups
> `_backups/2026-07-16-primary-docs-rollout/`.

Prepared 2026-07-16 for execution in a FRESH session. Owner-approved: fold the Sandy
primary-documents pilot (classes 1–5) into `/expand-city-sources` (done — Source 7 in
that SKILL.md) and roll it out to the other cities. Class 6 (`code_snapshot`) is NOT in
this rollout — see `PRIMARY_DOCS_PILOT_SPEC.md` §7/§10 for why (codifier hosts largely
auth-gated) and which codifier families would make it viable later.

## Read first, in order
1. `PRIMARY_DOCS_PILOT_SPEC.md` — the normative design + the Sandy results (STATUS block).
2. `.claude/skills/expand-city-sources/SKILL.md` **Source 7** — the per-city method
   contract (classifier gates, pipeline, index columns, acceptance test).
3. `sandy_city_council/packets/CLAUDE.md` + `classify_attachments.py` +
   `fetch_extract_text.py` — the reference implementation to adapt, not rewrite.
4. `SCHEMA_SPEC.md` §9 — the standardized trailing columns (`doc_class`, `fetch_status`,
   `sha256`, `text_path`, `text_chars`) and the sanctioned discard-binary exception.
5. `HANDOFF.md` — session gotchas (federation discipline, sqlite3 landmine, absolute paths).

## What is already done (do not redo)
- Sandy: complete (classes 1–5 + class-6 honest gap). The federated plumbing
  (`scripts/build_search_layer.py`: explicit `text_path` honoring, `doc_class` in
  `document` + `fts_packet`) is LIVE — no shared-script work needed.
- `polite_fetch.py`: comma-quoting bug FIXED + header-row guard added (batch files may
  now be headerless or start with a `url,name` header).
- `salt_lake_county/`: already stores staff-report text (fts_packet). OPTIONAL low-value
  cleanup: backfill `doc_class` labels on its packets index rows for taxonomy symmetry.

## Phase 0 — read-only TRIAGE (do this before any city work)
The pilot's easy mode was Sandy's per-attachment Legistar index (6,446 rows, all with
matter_id). The other 30 cities' `packets/` differ by portal family. One read-only pass
over every city's `packets/index.csv` + `packets/CLAUDE.md` buckets them:

- **Bucket A — per-attachment/per-document rows** (Legistar-like; Granicus cities whose
  packets dataset stores agenda-linked attachments as rows): full Source-7 treatment —
  classifier + fetch/extract per attachment. Expect the highest yield.
- **Bucket B — monolithic `full_packet` PDFs** (CivicPlus/Revize/CivicEngage pattern;
  often `stored_locally=no` index-only): classes are separable only if packet SECTIONS
  can be cut at high confidence. Default honest answer: classify at the packet level
  only where the title/agenda names a target class (e.g. "Council Member X memo"),
  fetch the packet, extract ONLY the identified section pages if cleanly separable,
  else record "classes not separable for this portal" in AVAILABILITY.md. Do NOT force it.
- **Bucket C — thin/empty packets datasets** (small towns; alta/copperton class):
  probably minutes-attachments and PMN notices only. An honest "no primary-doc corpus
  beyond what exists" is a valid, cheap completion.

Triage output: a table (city, portal family, bucket, row counts by packet_kind,
has-matter-metadata?, est. classified yield, priority) — write it into this file under
"## Triage results" and get owner sign-off on the priority order before bulk fetching
(the fetch volume across 30 cities is the one thing worth a checkpoint).

Priority heuristic (value-gated, not alphabetical): land-use-heavy bucket-A cities
first; the GP-text half (class 3) is valuable EVERYWHERE (every city has
`housing_plans/`) and is independent of the packets bucket — it can run for all cities
regardless.

## Triage results (Phase 0 — completed 2026-07-16, read-only; 5 parallel evidence agents + orchestrator rulings)

**Cross-cutting finding #1 — no city has Sandy's matter-metadata layer.** Sandy's
classifier keyed on the `legistar_matter` join; none of the other 30 has any
matter/item-level table. Every classifier in this rollout is **title + body +
in-title case/instrument tokens** (+ the MSD staff-report template header as an
in-TEXT detector for the township towns). The §5 precision/recall gates apply
unchanged — they're the safety net for the weaker inputs.

**Cross-cutting finding #2 — most Bucket-A text already exists on disk.** draper,
riverton, alta, copperton, emigration_canyon, kearns, lehi already carry full
`packets/text/` sidecar layers from the expand-sources waves. For them this rollout
is **classify-in-place** (add `doc_class` + link existing `text_path`) — near-zero
fetching. Only **logan** is a true Sandy-shaped fetch→extract→discard job.

**Cross-cutting finding #3 — class 3 (GP text) is ~done already.** 28/30 cities have
their current GP text sidecar in `housing_plans/`. Real remaining work: **west_valley**
(only the housing chapter extracted; GP is a componentized web product) and
**st_george** (GP stored as raw HTML chapters, no text sidecars). Optional extras:
draft-era chapters/station-area plans per the Sandy recovery tricks (incremental,
low-urgency), plus a small OCR queue of scanned MIH ordinances (herriman, murray,
magna, CH, white_city).

**Doc-drift flags found in passing** (fix during per-city execution, wrong-layer rule
observed): lehi + ogden `packets/CLAUDE.md` claim "no text corpus /
extraction_method=none" but real sidecar layers exist on disk (553 and 164 files —
verified real extractions, added by the later mandatory-sidecar retrofit).

### The table

| # | city | portal family | bucket | in-scope rows / total | existing text/ | est. classified yield | fetch needed | priority |
|---|------|---------------|--------|----------------------|----------------|----------------------|--------------|----------|
| 1 | draper | Granicus 3-era, per-attachment | **A** | 4,248 sr+exh / 4,721 | 3,592 ✅ | ~1,300–1,800 | no (classify-in-place; 507 index-only rows stay honest gaps) | **1** |
| 2 | riverton | Granicus 3-era, per-attachment (kind=filename heuristic — scan sr+exhibit together) | **A** | 2,702 / 3,015 | 2,493 ✅ | ~700–1,000 | no (classify-in-place; 402 index-only honest) | **1** |
| 3 | logan | Revize, per-DOCUMENT pointers, INDEX-ONLY | **A** | 867 staff_report / 1,124 | **0** | ~450–650 | **YES — the one true fetch job** (classified rows only; image-heavy → expect a big needs_ocr share) | **1** |
| 4 | lehi | Granicus, per-attachment, 2024–25 pilot window only | **A** | 452 / 564 | 553 ✅ (CLAUDE.md stale) | ~350–430 | no (raw on disk) — underscore-token regex needed | **2** |
| 5 | slc | PrimeGov council + slcdocs PC | **A-lite** (PC 2026 slice) + **B-no** (council) | 24 pre-typed PC staff_reports; 504 council full_packets 15–30 GB index-only | 39 (PC) | ~24 | no | **2** |
| 6 | emigration_canyon | PMN per-attachment | **A-lite** | 362 supp+sr / 375 | 324 ✅ | ~25–40 | no | **2** |
| 7 | copperton | PMN+GoDaddy per-attachment | **A-lite** | 210 / 305 | 240 ✅ | ~15–30 | no | **2** |
| 8 | alta | PMN per-attachment (staff analysis spans staff_report+supporting_doc) | **A-lite** | 589 / 847 | 830 ✅ | ~120–180 | no | **2** |
| 9 | kearns | PMN hybrid (9 broken-out staff reports + container bundles) | **A-lite** | 9 labeled / 80 | 79 ✅ | ~9 (containers stay unlabeled — honest) | no | **2** |
| 10 | cottonwood_heights | CivicEngage, stored full_packets | **B — SEPARABLE** (explicit `Appendix N - Staff Report/<title>` TOC = machine-readable split manifest) | 52 containers | 52 ✅ | ~30–60 cut sections | no | **3** |
| 11 | magna | PMN+CivicPlus, STORED born-digital full_packets | **B — SEPARABLE** (case-keyed `REZ/SUB/OAM` sections, `PLANNING STAFF RECOMMENDATION` headers; 63/296 sidecars flag staff reports) | 259 containers | 296 ✅ | ~100–200 cut sections | no | **3** |
| 12 | holladay | SuiteOne, stored full_packets | **B — borderline** (`COUNCIL STAFF REPORT` banners, no TOC; 2025+ floor, 78 packets) | 78 containers | 78 ✅ | ~40–80 if cut | no | **3** (owner call) |
| 13 | white_city | Streamline, stored full_packets | **B-no** (weak anchors, thin formal staff-report content; full-packet text already in FTS) | 99 containers | 99 ✅ | ~0 honest | no | **4** (doc-only) |
| 14 | millcreek | CivicEngage, stored-via-sibling | **B-no** (sampled "packets" are MINUTES-grade OCR text — packet↔minutes muddle; low net-new) | 552 rows | 244 ⚠ minutes-grade | ~0 honest | no | **4** (doc-only) |
| 15 | murray | CivicPlus Archive Center, INDEX-ONLY | **B-no now** (born-digital per docs — the one index-only city worth a FUTURE targeted fetch: 2023 packets are the only staff-analysis record of the lost-minutes era) | 339 full_packets, ~5.6 GB | 0 | 0 now; TODO note | would need fetch | **4** (doc + TODO) |
| 16 | bluffdale | CivicEngage AgendaCenter, INDEX-ONLY | **B-no now** (born-digital per docs, 2.85 GB; same future-fetch note) | 217 | 0 | 0 now | would need fetch | **4** (doc + TODO) |
| 17 | herriman | PrimeGov, INDEX-ONLY | **B-no** (image/map-heavy per own docs — vision/OCR only; 11.4 GB) | 372 | 0 | 0 honest | — | **4** (doc-only) |
| 18 | midvale | Revize, INDEX-ONLY | **B-no** (image-heavy, OCR-only; 7 dead links) | 117 | 0 | 0 honest | — | **4** (doc-only) |
| 19 | south_jordan | Municode Meetings, INDEX-ONLY | **B-no** (5.3 GB monolithic, generic titles) | 169 | 0 | 0 honest | — | **4** (doc-only) |
| 20 | south_salt_lake | CivicEngage `?packet=true`, INDEX-ONLY | **B-no** (3.4 GB monolithic) | 429 | 0 | 0 honest | — | **4** (doc-only) |
| 21 | st_george | Revize, INDEX-ONLY | **B-no** (7.5 GB image/plat-heavy) | 224 | 0 | 0 honest | — | **4** (doc-only) |
| 22 | west_jordan | PrimeGov, INDEX-ONLY | **B-no** (explicitly non-separable portal; 7.4 GB; 2025+ SPA era has NO packets at all) | 222 | 0 | 0 honest | — | **4** (doc-only) |
| 23 | provo | OnBase (session-gated, chunked-no-size) + CivicPlus PC | **B-no** (council fetch needs cookies; ~16 GB; PC 2022–24 thin) | 391 | 0 | 0 honest | — | **4** (doc-only) |
| 24 | park_city | CivicClerk, INDEX-ONLY | **B-no** (30 GB; titles are meeting names) | 468 packets | 474 (agendas only) | 0 honest | — | **4** (doc-only) |
| 25 | orem | CivicClerk, INDEX-ONLY | **B-no** (5.8 GB) | 204 packets | 220 (agendas only) | 0 honest | — | **4** (doc-only) |
| 26 | vineyard | CivicClerk, 100% INDEX-ONLY, no text layer at all | **B-no** (~7 GB, nothing on disk) | 119 packets | 0 | 0 honest | — | **4** (doc-only) |
| 27 | ogden | CivicEngage, stored THIN agendas | **C** (publishes NO staff reports — honest zeros; agenda text layer already built; CLAUDE.md stale) | 166 thin_agenda | 164 ✅ | 0 honest | — | **4** (doc fix) |
| 28 | west_valley | OnBase Agenda Online, stored thin agendas | **C** (hard ceiling — no packet layer exists) | 965 agendas | 965 ✅ | 0 honest | — | **4** + **class-3 GP gap** |
| 29 | nephi | CivicEngage AgendaCenter | **C** (agendas only — no packet type on portal) | 328 agendas | 323 ✅ | 0 honest | — | **4** (doc-only) |
| 30 | taylorsville | CivicPlus, current-cycle snapshot | **C** (7 docs; historical packets = honest publishing gap; GP text richest, already done) | 7 | 3 | ~2 | — | **4** (doc-only) |

### Proposed execution order (for owner sign-off)

- **Wave 1 (Bucket A, high yield):** draper, riverton, logan, lehi — 4 parallel agents.
  draper/riverton/lehi are classify-in-place; logan is the one bulk fetch
  (classified-rows-only, est. 450–650 docs, binary discarded per §9 exception).
- **Wave 2 (A-lite):** alta, copperton, emigration_canyon, kearns, slc(PC slice) —
  5 parallel cheap agents, classify-in-place.
- **Wave 3 (Bucket B section-cuts — stored, separable):** cottonwood_heights (TOC-anchored)
  + magna (case-key-anchored), and holladay if approved. Each cut section becomes a new
  index row (`packet_kind=packet_section`, additive) with its own text file; the parent
  full_packet row is untouched. Orchestrator (Fable) reviews every splitter's boundary
  sample before it writes.
- **Wave 4 (honest completions):** all 17 remaining cities get their AVAILABILITY.md
  "classes not separable for this portal / no corpus" record + stale-doc fixes
  (lehi, ogden) + TODO notes (murray/bluffdale future targeted fetch) — batched into
  2–3 doc-only agents.
- **Class-3 addenda (parallel to any wave):** west_valley full-GP text extraction;
  st_george HTML→text sidecars; the scanned-MIH OCR queue → TODO.
- **Optional, cheap:** salt_lake_county packets `doc_class` backfill for taxonomy symmetry.

**✅ OWNER SIGN-OFF 2026-07-16:** execution order approved as proposed (logan fetch
included); Bucket-B section-cuts scoped to **cottonwood_heights + magna only** —
holladay stays full-packet-text-only and gets the honest "not section-cut (banner
anchors only, no TOC)" record in Wave 4.

## Per-city execution (one focused agent per city — the proven pattern)
Follow SKILL.md Source 7 exactly. Non-negotiables, restated:
- Classifier with gates (≥95% sampled precision/class; recall sample iterated) BEFORE
  any bulk fetch; blank doc_class = honestly unclassified; empty classes are valid.
- Fetch politely (the fixed `polite_fetch.py`; headerless batch), extract, sha256,
  DISCARD binary (packets only — `housing_plans/` retains raws per ITS convention),
  `needs_ocr`/404 honest flags.
- Class 3 (GP text) goes in `housing_plans/`: draft-era chapters, amendment exhibits'
  plan text, station-area plans. Banked recovery tricks from Sandy: the city's old GP
  page in Wayback may carry the chapter list in embedded widget JSON; the ADOPTING
  ordinance often names the draft-of-record (its Legistar/packet attachments may be the
  only surviving copy); consultant plan-site domains rot (fetch NOW).
- Acceptance per city: validate_dataset PASS + 10-doc spot-check + the Sharkey-pattern
  test (one known consequential doc's FTS snippet returns its OWN text post-federation).
- Backups: `_backups/<date>-primary-docs-rollout/<city>/`. Agents do NOT regenerate
  `sources.csv`, do NOT run `build_cities_db.py`/`build_coverage.py`/`rebuild_derived.py`
  — ONE federation at the work-package boundary, run by the orchestrator, then re-run
  each batch city's `build_sources_index.py <slug>` and the per-city Sharkey-pattern
  FTS checks.
- Concurrency: batches of ~4–5 parallel city agents max (session-limit blast radius);
  disjoint city dirs; re-inventory on disk after any agent dies mid-run (the fetch log
  is the recovery ground truth — a killed agent's background fetch may have kept going).

## Closeout
Federate once; verify `fts_packet` growth ≈ the sum of new sidecars; run each city's
acceptance FTS query; update TODO.md (the Source-7 rollout item) + HANDOFF.md with a
dated record; report per-city yields + the honest-gap ledger. Queue the accumulated
`needs_ocr` rows as one repo-wide cf-vision-transcribe-style follow-up item.
