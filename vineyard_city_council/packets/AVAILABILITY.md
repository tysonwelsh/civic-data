# Vineyard packets — availability & gaps

Additive dataset: **agenda + agenda-packet (staff-report) documents** for Vineyard
City Council (incl. the 2014-era *Town Council*), Planning Commission, and the
Redevelopment Agency (RDA) board. Source of truth for what exists, the storage
decision, and honest gaps. `index.csv` is the machine-readable companion.

Retrieved 2026-07-05. Window **2014–2026** (short-history city; CivicClerk's earliest
event is 2014-01-08).

## Where the documents come from

Vineyard's portal is **CivicClerk (CivicPlus)**. Events are enumerated from the OData API
`https://vineyardut.api.civicclerk.com/v1/Events` (page size 15 — every page's
`@odata.nextLink` was followed; a bare `$top=N` is treated as a hard cap, not a page size,
and silently truncates). Each event carries a `publishedFiles[]` array of
`{fileId,type,name}`; document types are **Agenda**, **Agenda Packet**, and **Minutes**
(plus stray `Other`/`Notice`). Minutes are **excluded** — they already live as markdown
under `meeting_minutes/` (Council + RDA) and `planning_commission/`; duplicating them here
would violate the "never touch existing datasets" rule.

Each published file downloads from the collection-bound OData function
`Meetings/GetMeetingFileStream(fileId=<id>,plainText=false)` → `200 application/pdf`
(`plainText=true` → clean text). That fileId-keyed URL is the stable `source_url` on
every row. The null `agendaFile`/`minutesFile` scalar slots on the event are NOT the
documents — ignore them.

## Bodies harvested (3 — each joins to an existing vote dataset)

| categoryName (portal) | `body` in index | joins to |
|---|---|---|
| `City Council` (2014-era name: *Town Council*) | `Council` | `meeting_minutes/all_votes.csv` (body=Council) |
| `Planning Commission` | `PlanningCommission` | `planning_commission/all_votes.csv` |
| `Redevelopment Agency` | `RDA` | `meeting_minutes/all_votes.csv` (body=RDA) |

Other CivicClerk categories exist (ARCH Commission, Active Transportation, Library Board,
Youth Council, Development Review Committee, Public Notices, General, …) but carry no
roll-call vote dataset to join and are **out of scope** for this dataset — a deliberate
boundary, not a gap.

## Coverage (past events with documents), 2014-01 → 2026-06

Counts are of **past** events (dated on/before the 2026-07-05 retrieval); 18 future
Council + 57 future PC placeholder events carry no files yet (expected, not a gap).

| Body | Past events | w/ Agenda | w/ Agenda Packet | Neither |
|------|------------:|----------:|-----------------:|--------:|
| Council (incl. Town Council) | 378 | 369 | 63 | 6 |
| Planning Commission          | 304 | 302 | 34 | 2 |
| Redevelopment Agency (RDA)   | 138 | 136 | 22 | 0 |

**Documents indexed (this dataset): 926** — 807 Agendas + 119 Agenda Packets.

**Events present but with NO agenda-document** (honest zeros): of the 8 total, 6 are
**Cancelled / Test** events that legitimately never had an agenda:
Council `2024-02-28` (Cancelled), `2025-12-17` (Test Agenda), `2026-04-07`/`2026-06-02`/
`2026-06-16` (Cancelled work meetings); PC `2026-06-17` (Planning Commission, cancelled).
Only **2 are real meetings with no published agenda PDF**: Council `2023-04-26`
(City Council Meeting) and PC `2025-09-24` (Joint PC + City Council). Recorded, not filled.

### Join coverage to the vote datasets
Every PC vote-date (78/78) and every RDA vote-date (9/9), and 144/145 Council vote-dates,
have a matching agenda/packet here. Because the packet set reaches back to **2014** while
votes begin **2020**, the document set is far larger than the vote set — that historical
reach (2014–2019) is the dataset's additive value.

## Council-vs-PC-vs-RDA asymmetry (logged, not forced)

- **Agendas** are near-universal for every body (Council 98%, PC 99% of past events);
  **Agenda Packets are the exception, not the rule** — Council 17% (63/378), PC 11%
  (34/304), RDA 16% (22/138). Most Vineyard meetings publish only an Agenda.
- **PC packets are physically the largest** — avg **54.8 MB** (n=34) vs Council **17.9 MB**
  (n=62) vs RDA **1.96 MB** (n=22). PC staff reports carry plats, site plans, and
  renderings; RDA packets are thin. Same pattern seen in Orem.

## Storage decision — INDEX-ONLY (size math)

**Mode: INDEX-ONLY. Zero document bodies are stored locally.** Every row has a live
fileId-keyed `source_url`, `format=na`, `stored_locally=no`, empty `path`, and `size_mb`
where a Content-Length probe captured it.

Size math (streamed-GET Content-Length; the API rejects HEAD with 405 and ignores Range,
so sizes come from a streamed GET whose body is not read):

| Document | Files | Sized | Total (sized) | Avg | Max |
|----------|------:|------:|--------------:|----:|----:|
| Agenda Packets | 119 | 118 | **3,011.8 MB** | 25.5 MB | 351.7 MB |
| Agendas        | 807 | 39 (sample) | 201.7 MB sampled | **5.17 MB** | 59.9 MB |

**Sizes are partial (the probe was not exhaustive):** all but one Agenda Packet is sized;
Agendas were sampled (39 of 807). Unlike Orem — whose Agendas were 0.1 MB born-digital
outlines — **Vineyard bundles attachments into the "Agenda" file**, so agendas here
average **5.17 MB** (max 59.9 MB). Estimated Agenda total ≈ 807 × 5.17 MB ≈ **4.2 GB**.

Full-corpus estimate ≈ **3.0 GB packets + 4.2 GB agendas ≈ 7.2 GB** — roughly **18× the
~400 MB local-store budget**, and even the Agenda-only layer (~4.2 GB) is ~10× budget. No
clean sub-budget layer exists (Vineyard has no tiny-outline agenda tier), so the whole
corpus is index-only. Nothing is silently capped or dropped: all 926 documents are
enumerated and retrievable from their `source_url`; only the bytes are left on the portal.
To materialize any document later, GET its `source_url`; to bulk-fetch a subset, filter
`index.csv` on `body`/`packet_kind`/`date`.

`raw/` therefore contains only `_fetch_log.jsonl` (one line per document: the size-probe
provenance — url, probed `content_length`, body not downloaded). This is a valid
index-only dataset (validated).

## Not built

- **No stored PDFs and no extracted-text corpus** (index-only). `format=na` on every row;
  `screen_corpus.py` does not apply (no text corpus to screen).
- **Minutes** — intentionally excluded (already in `meeting_minutes/` + `planning_commission/`).
- **Non-vote boards/commissions** (ARCH, Library, Youth Council, DRC, Public Notices,
  General, …) — out of scope; no vote dataset to join.

## Primary-document classes (doc_class rollout, 2026-07-16)

Ruled **Bucket B-no** in `../../PRIMARY_DOCS_ROLLOUT.md` (triage table; Wave 4, doc-only).
The four packet-attachment primary-document classes (staff reports, memos, development
agreements, plan amendments) are **not separable** for this portal — an honest **no** for all
four. No fetch, no classification was performed.

Why not separable: **all 926 index rows are index-only** (nothing stored on disk, no text
layer at all), and only **119** of them are Agenda Packets — most Vineyard meetings publish an
agenda only. The full corpus is **~7 GB**, and the monolithic CivicClerk bundles carry no
per-attachment metadata to cut on, so class-labeled sections cannot be produced at confidence.
Class 3 (General Plan text) is independent and lives in `housing_plans/`.
