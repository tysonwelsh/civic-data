# Kearns — agenda packets / staff reports: availability

**As-of:** 2026-07-13 · **Mode:** STORED (born-digital PDFs on disk) · **Source:**
Utah Public Notice (PMN) only.

## Source note — PMN, not the city site

`kearns.utah.gov` is a **Cloudflare-blocked custom CMS** (JS challenge to every bot,
browser UA included) and is **not scrapable**. All packets here come from the **Utah
Public Notice Website** (`utah.gov/pmn`), which serves clean-text PDFs to a plain
browser UA:

- **Council packet** — PMN public body **5823** ("Kearns Council"). Each city-era
  notice carries a single bundled **"Meeting Agenda with Supporting Documents" /
  "Meeting Supporting Documents" / "Agenda Packet"** PDF (agenda + ordinance/resolution
  texts + exhibits — distinct from the separately-posted Meeting Minutes and the
  agenda-only PDF). The CRA (Community Reinvestment Agency), which the council convenes
  in-recess, posts its own supporting-documents packet on the same body (1 found,
  2025-07-14; `body=CRA`).
- **PC packet / staff report** — PMN public body **1561** (the Kearns Planning
  Commission, **MSD-staffed**). Each notice carries a bundled **`YYMMDD_KearnsPC_Packet.pdf`**
  (older era `YYMMDD_Kearns[TPC|MetroTC]_Packet.pdf` / `YYMMDD_Kearns_Packet_Final.pdf`)
  and, on land-use items, one or more standalone **staff reports** keyed to the
  `OAM/REZ/CUP/VAR<YYYY>-<NNNNNN>` case number.

Enumeration was done from the **cumulative notice list**
(`/pmn/list/notices.html?id=<body>&page=400`, a single GET returning the body's entire
history — the body page and the 6-month list view otherwise surface only ~10 notices).
The minutes/agenda-only/MP3-audio attachments were dropped;
`crawl_notices_kearns.py` classifies every attachment and its `_candidates_<body>.csv`
records the full drop/keep decision.

## Coverage (STORED — 80 files, 584 MB)

| Body | Packets | Window | Kinds |
|---|---|---|---|
| Council | 27 | 2023-04-18, then 2024-07-08 → 2026-07-13 | 26 full_packet + 1 staff_report |
| CRA | 1 | 2025-07-14 | 1 full_packet |
| PC | 52 | 2019-01-14 → 2026-07-06 | 44 full_packet + 8 staff_report |

- Council packet years: 2023 ×1 (a standalone Titles 18/19 staff report), 2024 ×7,
  2025 ×13, 2026 ×7.
- 79 of 80 are born-digital `format=text` (`pdftotext -layout`). **One** council packet
  (`AgendaPacket07082024.pdf`, 2024-07-08) is an **image-only scan** (`format=scanned`,
  no text sidecar — vision/OCR required to read it).

## Gaps — honest, verified

1. **Township-era council packets were never published as a bundled packet
   (2017-01 → 2024-06).** On PMN body 5823 the township council notices carry only an
   agenda (a short `MM-DD-YY.pdf`) plus **loose individual** ordinance/resolution/budget
   PDFs — there is **no single "supporting documents" packet** the way the city era
   produces one. Those loose ordinance texts are proper **`ordinances/` dataset** content
   (source 3), not a meeting packet, so they are deliberately NOT indexed here. This is a
   **publishing-pattern gap**, not a scraper miss: the bundled-packet convention begins
   with the city era (first bundled council packet = 2024-07-08). The earliest council item
   captured is a 2023-04-18 standalone staff report.

2. **PC packets 2011-10 → 2018-12 are PMN-purged (41 files, `unrecovered.csv`).** These
   notices list a `..._Packet.pdf`, but the file blob returns **HTTP 404** — every PMN
   `file_id < ~457000` (pre-~mid-2018) has been removed from PMN storage. This is the same
   file-rot boundary that hit the council-minutes back-catalog (see
   `meeting_minutes/minutes_unrecovered.csv`). Recoverable only if PMN restores the blobs;
   not on the Internet Archive. Distribution: 2011 ×1, 2012 ×7, 2013 ×4, 2014 ×3, 2015 ×3,
   2016 ×5, 2017 ×8, 2018 ×10.

3. **PC pre-2017 packets are below the entity data floor (2017).** Kearns Metro Township
   took effect 2017-01-01; the 2011-2016 Kearns PC packets (all purged anyway, see gap 2)
   predate incorporation and would be bonus context only.

4. **Cancelled PC meetings** (`YYMMDD_KearnsPC_Cancelled.pdf`, 81 across the record) carry
   no packet — correctly excluded, not a gap.

## Primary-document text layer (`doc_class`, 2026-07-16)

Classify-in-place over the STORED corpus (no fetching): `classify_attachments.py` adds
the §9 columns `doc_class,fetch_status,sha256,text_path,text_chars`.
**10 rows labeled `staff_report`** (whole-class verified against the MSD template
header, precision 10/10) = the 9 broken-out per-item staff reports (PC 8 / Council 1)
**+ 1 recall-gate catch** (`OAM2025-001330 - P.C. packet.pdf`, 2025-03-03 — a single
standalone MSD staff report mis-shelved as `full_packet` by its filename; `packet_kind`
left verbatim, `doc_class=staff_report`). The **71 `full_packet` containers stay
unlabeled** (their full-packet text already serves FTS; a container is not a
staff_report even when dominated by one). `member_memo`, `plan_amendment`,
`development_agreement` are **honest empties** — no broken-out instances (title +
sidecar-head sweep of all 80 rows). The 1 scanned council packet
(`AgendaPacket07082024.pdf`) is a container with no sidecar → stays unlabeled. Full
method + boundary decisions in `CLAUDE.md`.

## Size / mode decision

Full stored set = 80 fetchable packets = **584 MB** (largest single file 64.8 MB;
`CUP2025-001399_Staff_Report_Final.pdf`). Well under the ~1.5 GB budget → **STORED**
(raw PDFs retained under `raw/<date>/` + `raw/_fetch_log.jsonl`; text sidecars under
`text/`). No `--max-bytes` cap was applied (it would drop whole meetings).
