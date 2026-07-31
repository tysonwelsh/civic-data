# packets/ — availability, size math, and mode decision — as-of 2026-07-13

Source 1 (agenda packets / staff reports) of `expand-city-sources`, for Herriman City.
**Mode: INDEX-ONLY** (no packet PDFs stored locally) — see the size math below.

## What was checked

1. **PrimeGov archive API** (`herriman.primegov.com`), 2020–2026:
   `GET /api/v2/PublicPortal/ListArchivedMeetings?year=YYYY` (browser UA). Meeting counts:
   2020 = **0** (PrimeGov starts 2021-01-07, same as the minutes layer), 2021 = 82,
   2022 = 87, 2023 = 74, 2024 = 74, 2025 = 77, 2026 = 46 (through 2026-07-13).
   Each meeting's `documentList[]` was classified by `templateName`; packet-type documents
   are `Packet` (340 across the in-scope bodies) and one `HTML Mini-Packet`.
   In-scope bodies (committeeId): Council **3**, Planning Commission **14**, CDRA **4**,
   HCFSA **8**, HCSEA **9**, Joint CC/PC **12**. Out-of-scope committees with packets
   (Youth Council 16, Arts Council 1, Appeal Authority 7, trails/health/veterans boards)
   were deliberately not cataloged.
2. **Every packet's size** was probed with a polite ranged GET (`Range: bytes=0-0`;
   1 req/s) against `/Public/CompiledDocument?meetingTemplateId=<templateId>`, following
   the 302 to the Azure blob and reading `Content-Range` for the full byte size. **The
   host mis-handles HEAD** (302 → `/Errors/NotFound`), so `polite_fetch.py --size-only`
   was replaced by the ranged-GET equivalent; no packet body was downloaded (1 byte per
   probe). All probes logged in `raw/_fetch_log.jsonl`.
3. **The 2020 floor year** (absent from PrimeGov) was checked on the legacy pre-PrimeGov
   AWS S3 bucket (`s3-us-west-1.amazonaws.com/herriman-agendas/`, listing AccessDenied but
   objects live) — **it DOES hold 2020 packets**, in `2020-agendas/2020-city-council-packets/`
   and `2020-agendas/2020-planning-commission-packets/`. Keys were harvested from
   Wayback-archived `herriman.org/agendas-and-minutes/` snapshots (2020-01-22, 2020-03-04,
   2020-09-26, 2020-11-01, 2021-01-24) plus HEAD-probes of every 2020 meeting date in the
   repo's minutes indexes and the plausible cadence grid. **25 council-family + 7 PC 2020
   packets are live** (HTTP 200, HEAD-probed sizes).

## Size math → INDEX-ONLY decision

| Year | packets | bytes |
|---|---|---|
| 2020 (S3) | 32 | 1.70 GiB |
| 2021 | 82 | 2.85 GiB |
| 2022 | 61 | 2.32 GiB |
| 2023 | 59 | 1.47 GiB |
| 2024 | 49 | 1.00 GiB |
| 2025 | 52 | 1.23 GiB |
| 2026 | 37 | 0.87 GiB |
| **Total** | **372** | **11.43 GiB** (12,274,378,587 bytes) |

Per-packet: min 27 KB, **median 17.4 MB**, max **297 MB**. Herriman packets are bundled
whole-meeting compiled PDFs (agenda + all staff reports + all exhibits — maps, plats,
site plans), the same document model as West Jordan (same PrimeGov vendor). 11.43 GiB is
~7.6× the ~1.5 GB budget, so — like West Jordan, bluffdale, and murray — this dataset is
a **link index**: every packet is cataloged in `index.csv` with a live `source_url` +
byte size (`stored_locally=no`, `format=na`, empty `path`), and nothing is stored under
`raw/` except the probe provenance log. This is the documented, allowed exception to
"retain every raw original" (the files are public and re-fetchable; reading one requires
vision/OCR, not `pdftotext`). See `CLAUDE.md` for how to fetch one on demand.

## Coverage (372 rows, 2020-01-08 → 2026-07-08)

Per body: **Council 190 · PlanningCommission 121 · CDRA 19 · HCSEA 18 · HCFSA 16 ·
JointCCPC 8.** Bytes per body: Council 6.76 GiB, PC 4.32 GiB, agencies+joint 0.34 GiB.

Recorded-vote dates covered by a packet (packet date == vote date):

| Year | council-family | PC |
|---|---|---|
| 2020 | 16/22 | 6/18 |
| 2021 | 35/35 | 17/17 |
| 2022 | 20/23 | 17/17 |
| 2023 | 21/21 | 18/19 |
| 2024 | 22/22 | 17/21 |
| 2025 | 22/27 | 18/19 |
| 2026 | 9/9 | 10/10 |

PrimeGov-era (2021+) coverage is near-total; every gap below is a meeting whose
`documentList` simply has no `Packet` entry (a publishing pattern, not a scraper miss).

## Gaps and quirks (honest — none filled)

- **2020 is PARTIAL by source.** The S3 bucket holds packets for only part of 2020:
  **no council packets for 2020-04-08, 04-22, 05-06, 09-09(CDA), 11-18(SCCM), 12-16**, and
  **no PC packets for 12 of the 19 PC minutes dates** (only 02-20, 03-05, 04-02, 06-18,
  07-16, 09-03, 12-03 exist). The gap is concentrated in the COVID-remote era
  (April–early-May 2020) and scattered PC dates; the Wayback page snapshots from the
  period confirm those packet links were never published. All misses returned S3 403
  (= key absent under a list-denied bucket) for both the plain and the `+Packet` key
  grammar (below).
- **Two 2020 S3 key grammars.** Jan–Feb + most fall 2020 packets are keyed
  `YYYY_MM_DD[_SUFFIX].pdf`; March–Sept 2020 packets use a `+`-joined grammar
  `YYYY_MM_DD+[QUALIFIER+]Packet.pdf` (e.g. `2020_03_11+Packet.pdf`,
  `2020_05_27+HCSEA+Packet.pdf`, `2020_07_08+RCCM+Packet.pdf`, `2020_09_30+SCCM+Packet.pdf`).
  Both grammars were probed for every candidate date. Qualifiers: `CDA` = CDRA,
  `HCSEA`, `RCCM` = regular council, `CCW` = council work, `SCCM` = special council.
- **Six packet dates have NO minutes in the repo's 2020 layer** (2020-05-13, 07-29,
  09-23, 11-05, 12-09 council-family; 2020-12-03 PC) — the packet proves a meeting was
  *scheduled*; whether minutes were ever produced is unknown (2020 interior minutes gaps
  were previously attributed to COVID cancellations). Logged here as a cross-dataset
  observation; the minutes layer was NOT modified. PrimeGov-era packet-only dates
  (e.g. 2022-08-10, 2023-08-30, 2025-04-30, and mid-2026 dates whose minutes are simply
  not yet published) are the same phenomenon.
- **One `HTML Mini-Packet` (2024-01-24 council, templateId 1713) is EXCLUDED** from
  `index.csv`: its `CompiledDocument` URL returns PrimeGov's `PublishedDocumentError`
  page (it is an HTML-rendered template, not a compiled PDF). The same meeting's normal
  `Packet` (templateId 1712, 16.7 MB) is indexed.
- **PrimeGov meetings without packets** (2021–2026, in-scope bodies): 6 council regular,
  5 council special, 1 council strategic, 4 ceremonial, 2 canvass, 7 Joint CC/PC regular,
  12 PC regular meetings carry no packet document; cancelled meetings carry none. These
  are honest publishing gaps.
- **2019 packets exist on the S3 bucket** (`2019-agendas/2019-city-council-packets/`,
  25 keys seen in Wayback) — **below the repo's 2020 data floor; deliberately not
  cataloged.**
- **The S3 bucket is a legacy host with no longevity guarantee.** The 32 2020 rows'
  `source_url`s serve today (HEAD 200, 2026-07-13) but could be retired at any time;
  if 2020 packets matter long-term, mirror them promptly (~1.7 GiB).
- **PrimeGov blob URLs are time-limited** — always fetch via the indexed
  `CompiledDocument?meetingTemplateId=` URL (it mints a fresh SAS), never a cached
  `pgwest.blob.core.windows.net` URL.

## Provenance

`raw/_fetch_log.jsonl` — 435 probe records (341 PrimeGov ranged GETs + 1 retry, 45 + 48
S3 HEAD probes incl. every negative), each with url / http_status / bytes_total /
retrieved_utc. Probes ran 2026-07-13 at ≥1 s/host. No packet body was downloaded.

## Primary-document classes (doc_class rollout, 2026-07-16)

**Ruling: honest no — the per-attachment primary-document classes are not separable for
this portal.** Under the repo-wide primary-documents rollout (`PRIMARY_DOCS_ROLLOUT.md`,
triage 2026-07-16) Herriman was bucketed **B-no**. The four attachment-borne doc_class
classes — `staff_report`, `member_memo`, `plan_amendment`, `development_agreement` — cannot
be extracted here because:

- All **372 packets are INDEX-ONLY, whole-meeting compiled PDFs** (11.43 GiB; median
  17.4 MB, max 297 MB) — one bundled document per meeting, not per-item rows. PrimeGov
  exposes **no separable per-item staff-report PDFs** and no matter/item-level metadata to
  key a classifier on (the rollout's cross-cutting finding: no non-Sandy city has a matter
  layer).
- The packets are **image/map/plat-heavy** — by this dataset's own record reading one
  requires **vision/OCR, not `pdftotext`** — so there is no cheap high-confidence
  section-cut path either.

Nothing is fetched, classified, or section-cut in this rollout; no `doc_class`/`text_path`
column is added and no packet body is downloaded. Class 3 (`general_plan`) is out of scope
for `packets/` — Herriman's GP text already lives in `housing_plans/`. The `index.csv`
link index remains the honest, complete record of what Herriman publishes.
