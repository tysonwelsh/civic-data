# Orem packets — availability & gaps

Additive dataset: **agenda + agenda-packet (staff-report) PDFs** for Orem City Council,
Planning Commission, and Board of Adjustments. Source of truth for what exists, what is
stored locally, what is index-only, and what could not be recovered. `index.csv` is the
machine-readable companion; this file is the honest-gaps narrative.

Retrieved 2026-07-05. Window 2020–2026.

## Where the documents come from

Orem's portal is **CivicClerk (CivicPlus)**. Council/PC/BoA events are enumerated from
the OData API `https://oremut.api.civicclerk.com/v1/Events`. Each event carries a
`publishedFiles[]` array; the document types are **Agenda** (`fileType 1`, a 1–2 page
born-digital outline PDF), **Agenda Packet** (`fileType 2`, the full staff-report bundle),
and **Minutes** (`fileType 4`). Minutes are **excluded** from this dataset — they already
live as markdown under `meeting_minutes/` and `planning_commission/`; duplicating them
here would violate the "never touch existing datasets" rule.

Each published file downloads from the (unbound-collection) OData function
`Meetings/GetMeetingFileStream(fileId=<id>,plainText=false)` → `200 application/pdf`.
That fileId-keyed URL is the stable `source_url` for every row, stored or not.

## Coverage (events with documents), 2021-07 → 2026-06

CivicClerk holds events from **2021-07-13** (Council) / **2021-07-21** (PC) forward.

| Body | Past events* | Agenda | Agenda Packet | No files |
|------|-------------:|-------:|--------------:|---------:|
| City Council (`Council`)            | 113 | 113 | 99  | 0 |
| Planning Commission (`PlanningCommission`) | 104 | 103 | 100 | 1 |
| Board of Adjustments (`BoardOfAdjustment`) | 7   | 5   | 5   | 2 |

\* Events dated on/before the 2026-07-05 retrieval. **22 future placeholder events**
(9 Council 2026-07→12, 13 PC 2026-07→2027-01) carry no files yet — expected, not a gap.

**Events present but with NO published documents** (honest zeros — the meeting happened,
the city published no agenda/packet PDF):
- PC `2021-11-17`
- BoA `2021-11-24`, `2021-12-22`

**Council-vs-PC asymmetry** (logged, not forced): every past Council meeting has an
Agenda PDF (113/113) but only 88% carry a full Agenda Packet (99/113 — 14 meetings are
agenda-only). PC publishes packets more consistently (100/104 ≈ 96%). PC packets are also
physically larger (avg **31.6 MB** vs Council **21.8 MB**) — PC staff reports carry plats,
site plans, and renderings. BoA packets are enormous (avg **89 MB**, n=5).

## Storage decision — size math (the reason most rows are index-only)

Full corpus HEAD/stream-probed 2026-07-05 (Content-Length; the API rejects HEAD with 405,
so sizes come from a streamed GET whose body is not read):

| Document | Files | Total | Avg |
|----------|------:|------:|----:|
| Agendas (all bodies)        | 221 | **36.3 MB** | 0.16 MB |
| Agenda Packets (all bodies) | 204 | **5,760 MB** | 28.2 MB |
| **Grand total**             | 425 | **5,796 MB (5.8 GB)** | |

The packet corpus is **~14× the ~400 MB budget**. Decision:

- **All 221 Agenda PDFs are stored locally** (`raw/<date>/<body>_e<eventid>_agenda.pdf`),
  36.3 MB total — complete, well under budget. `stored_locally=yes`, `format=text`.
- **All 204 Agenda Packets are index-only** (`stored_locally=no`, `format=na`, empty
  `path`) — each row keeps its live fileId-keyed `source_url` and measured `size_mb`.
  Nothing is silently capped or dropped: every packet is enumerated and retrievable from
  its URL; only the ~5.8 GB of bytes are left on the portal.

This is a clean, reproducible rule (store the small complete layer; index the bulky one)
rather than an arbitrary partial download. To materialize any packet later, GET its
`source_url`. To bulk-fetch a subset, filter `index.csv` on `packet_kind=agenda_packet`.

## Pre-CivicClerk window (2020-01 → 2021-06) — NOT recovered

CivicClerk's earliest event is 2021-07. Council/PC minutes for 2020–2021-H1 exist in the
repo (sourced from a Google Drive archive), but the matching **agenda packets** for that
window live only in the Drive archive's agenda folders, which could not be enumerated
GET-only:

- Root: `https://drive.google.com/drive/folders/1EEBkHidmn6PrXj9ib0thApFSqmgU9QSv`
- Folder **"Agendas"** = `1bYGd-3jyVsNPFpQfbQeipHqr8xzWcivm`
- Folder **"Agendas-City Council"** = `1jCLlNKyu1yGkYyefk0YM6cPG3_d90unz`

Google Drive folder *children* are loaded via an authenticated `batchexecute` POST, not
the static folder HTML (which contains only the folder's own metadata). The polite fetcher
is GET-only, so the child listing cannot be harvested without the Drive API / an
authenticated Drive MCP. **Deferred** — see repo `TODO.md`. This is a real acquisition gap,
recorded here rather than faked.

## Not built

- **No extracted-text corpus.** This dataset stores raw born-digital PDFs only; there is
  no per-document text CSV, so `screen_corpus.py` (a text-anomaly screen) does not apply.
  Agenda PDFs are born-digital (`format=text`) and text-extractable on demand.
- **Minutes** — intentionally excluded (already in `meeting_minutes/` + `planning_commission/`).

## Primary-document classes (doc_class rollout, 2026-07-16)

Ruled **Bucket B-no** in `../../PRIMARY_DOCS_ROLLOUT.md` (triage table; Wave 4, doc-only).
The four packet-attachment primary-document classes (staff reports, memos, development
agreements, plan amendments) are **not separable** for this portal — an honest **no** for all
four. No fetch, no classification was performed.

Why not separable: the 204 CivicClerk **agenda_packets** are **index-only** (nothing on disk,
no text layer), **5.8 GB** total, avg **28 MB**, and carry meeting-name titles only (no
per-attachment / per-item metadata) — each is a monolithic whole-meeting bundle that cannot be
cut into class-labeled sections at high confidence. The stored **agendas** are thin outlines,
not staff-report content. Pre-2021-06 packets remain the known unrecovered window (the Google
Drive auth gap recorded above). Class 3 (General Plan text) is independent and lives in
`housing_plans/`.
