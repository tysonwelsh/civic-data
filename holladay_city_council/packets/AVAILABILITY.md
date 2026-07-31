# Holladay packets — availability & gaps

Additive dataset: **whole-meeting agenda packets** (agenda + staff reports + exhibits) for
Holladay **City Council**, **Planning Commission**, in-session **RDA Board**, and **LBA**,
harvested from the city-native **SuiteOne** meeting portal. This file is the source of truth
for what exists, the storage decision, and the honest coverage floor. `index.csv` is the
machine-readable companion.

Retrieved **2026-07-13**. **Mode: STORED** (all 78 packets on disk; 909 MB raw + 49 MB text
sidecars, under the ~1.45 GB budget). Window **2025-01-02 → 2026-09-01** (upcoming 2026
agenda packets are posted ahead of the meeting). Council meets **Thursday**; PC modal-**Tuesday**.

## Where the documents come from — the three-channel split

Holladay publishes across three channels (recon §1). For **agenda packets** specifically:

| Channel | Holds packets? | Coverage | Verdict |
|---|---|---|---|
| **SuiteOne** (`holladayut.suiteonemedia.com`) | **YES** — whole-meeting "Agenda Packet" per event | **2025-01-02 → present** | ✅ the packet source; STORED here |
| **Revize Document Center** (`holladayut.gov` → `cms3.revize.com`) | Only current-year **meeting-schedule** PDFs are exposed; the agendas page now just **iframe-embeds SuiteOne** | current schedules only | no browsable packet back-catalog |
| **Utah PMN** (bodies 388/389) | agenda/minutes attachments; occasional packet PDFs per notice | pre-2020 → present | minutes spine (source 4 territory), not a packet archive |

**SuiteOne is shallow by design** — its data begins **early 2025**. Confirmed three ways:
(1) the unfiltered server-rendered Recent-Events table returns everything from **2025-01-02**;
(2) event IDs below ~2650 (500/1000/1500/2000/2400) all return the portal's "error / does not
exist" page — there is no pre-2025 event space; (3) recon independently observed the same floor.
The portal's date-range/keyword **search is POST-only** (`/Home/GetRecentEvents`,
`/Home/SearchEvents` as a route 404s), which the polite GET-only rule and `polite_fetch.py`
do not use — but since the *unfiltered* dump already reaches the true floor, nothing is hidden
behind it.

### Pre-2025 packets (2020–2024) — a genuine publishing gap, not a scraper miss
There is **no retrievable agenda-packet archive before 2025**:
- SuiteOne has no pre-2025 events (above).
- The Revize Document Center exposes only current meeting-schedule PDFs; the agendas page
  delegates entirely to the SuiteOne iframe, and its "Archive" link (`archive/index.php`) 404s.
- **Wayback Machine has zero archived agenda/packet PDFs** for either `holladayut.gov` or the
  legacy `cityofholladay.com` (CDX `mimetype:application/pdf` → 0 rows on both domains).

For 2020–2024, the city posted **agendas + minutes** (the minutes already live in
`meeting_minutes/` and `planning_commission/`, sourced from PMN). Recovering any pre-2025
staff-report packets would require **per-notice PMN attachment crawling** (expansion source 4,
PMN backfill) or a **GRAMA request** — out of scope for this SuiteOne-based packets dataset and
logged here as the honest floor.

## SuiteOne enumeration method

The portal landing page (`GET https://holladayut.suiteonemedia.com/`) server-side-renders a
"Recent Events" table with one `<tr>` per meeting: title (→ body), a `.NET`-ticks date, and up
to three document links — Agenda (`/event/GetAgendaFile/Agenda?aid=`), **Agenda Packet**
(`/event/GetAgendaPacketFile/Packet?apid=`), and Minutes (`/event/GetMinutesFile/Minutes?mid=`).
`parse_suiteone_events_holladay.py` parses that table; `fetch_packets_holladay.py` GETs each
event's whole-meeting **Agenda Packet** (the `apid` bundle = the staff-report packet, distinct
from the thin `aid` agenda).

**SuiteOne quirks (verified 2026-07-13, worth adding to recon):**
- The packet route **rejects HEAD** (`GetAgendaPacketFile` → 404 to HEAD) and **ignores Range**
  (`Range: 0-0` returns full 200), so `polite_fetch.py --size-only` cannot size these — a full
  GET is the only way to learn Content-Length. Sizing was therefore folded into the store pass
  with a running budget guard (never triggered; total 953 MB < 1.45 GB).
- The label segment after `GetAgendaPacketFile/` is cosmetic: both `.../Packet?apid=N` and the
  page's `.../Agenda%20Packet?apid=N` return the same PDF.
- 9 SuiteOne bodies exist; category codes: City Council=26, Planning Commission=27, RDA Board=32
  (LBA has no distinct search category — it appears as its own events). Only the four
  vote-bearing bodies (Council/PC/RDA/LBA) were harvested; Arts Council, Historical Commission,
  Tree Committee, Admin Hearing Officer, Design Review Board, Board of Canvassers are out of
  scope (no vote dataset to join).

## What was harvested (78 packets, all born-digital text)

| body | n | window | size |
|---|---|---|---|
| Council | 36 | 2025-01-09 → 2026-07-16 | 447.8 MB |
| PlanningCommission | 29 | 2025-01-07 → 2026-07-07 | 494.8 MB |
| RDA | 7 | 2025-05-01 → 2026-06-11 | 5.2 MB |
| LBA | 6 | 2025-09-18 → 2026-06-11 | 5.1 MB |
| **total** | **78** | **2025-01-02 → 2026-09-01** | **952.9 MB** |

- **RDA and LBA carry their own SuiteOne packet events** (separate from in-session RDA/LBA in the
  council minutes) — confirmed present and included. Their packets are small agenda-only bundles.
- **All 78 are born-digital** (`pdftotext -layout` → text sidecar for every one; extraction log:
  78/78 `extracted`, 0 image-only). Sidecars in `text/` feed `cities.db fts_packet`.
- `screen_corpus.py`: 0 read errors, healthy dict_ratio (median 0.78); a handful of
  weird-char/split-word outliers are the normal signature of embedded exhibit tables, plats,
  and site-plan text inside whole-meeting bundles — spot-checked as legible packet content, not
  extraction corruption.

## Join to the vote datasets
`index.csv` is keyed by `date` + `body`. Of the packet dates, 28/36 Council and 13/29 PC align
to a `date` in the corresponding `all_votes.csv`; the unmatched are recent/upcoming 2026
meetings whose minutes have not yet posted to PMN (the repo minutes lag SuiteOne agendas) and
a few meetings that recorded no roll-call vote. This is expected, not a defect.

## Not included / honest gaps
- **Pre-2025 packets** — none published/retrievable (see above).
- **Thin agendas** (`aid`) and **minutes** (`mid`) on SuiteOne were **not** re-harvested here:
  minutes already live in `meeting_minutes/`/`planning_commission/`; the packet (`apid`) already
  embeds the agenda.
- **Non-vote-bearing bodies** (Arts Council, Historical Commission, Tree Committee, Admin
  Hearing Officer, Design Review Board, Board of Canvassers) — out of scope by design.

## Primary-document classes (doc_class rollout, 2026-07-16)

Assessed as part of the repo-wide primary-documents rollout (`PRIMARY_DOCS_ROLLOUT.md`,
Source-7 doc_class taxonomy: staff_report / exhibit / presentation / correspondence / GP text).
**Ruling: NOT section-cut** (owner decision, 2026-07-16 — Wave 3 scoped to
cottonwood_heights + magna only). The 78 STORED `full_packet` bundles carry `COUNCIL STAFF
REPORT` banners but **no table of contents** — banner anchors only, which sit below the
cut-confidence bar, so the four attachment classes are **not row-separable** for this SuiteOne
portal. No per-class `packet_section` rows were created. The 78 born-digital full-packet text
sidecars (`text/`) already serve `cities.db fts_packet`, so packet staff-report text is fully
searchable at the whole-meeting granularity. Classes were assessed, not forgotten.
