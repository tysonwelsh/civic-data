# Park City packets — availability & gaps

Additive dataset: **agenda + agenda-packet (staff-report) documents** for Park City
**City Council**, **Planning Commission**, and the **Historic Preservation Board (HPB)**,
harvested from the CivicClerk (CivicPlus) OData API. Source of truth for what exists, the
storage decision, and honest gaps. `index.csv` is the machine-readable companion.

Retrieved **2026-07-05**. Window **2020–2026** (Council meets **Thursday**; 5 at-large
members + a Mayor who votes only to break ties).

## Where the documents come from

Park City's portal is **CivicClerk (CivicPlus)**. Events are enumerated from the OData API
`https://parkcityut.api.civicclerk.com/v1/Events` (page size 15 — every page's
`@odata.nextLink` was followed; a bare `$top=N` is a hard result **cap**, not a page size,
and silently truncates, so it was not used). Each event carries an inline
`publishedFiles[]` array of `{fileId,type,name,url}`; document `type` values are
**Agenda**, **Agenda Packet**, **Minutes**, and stray **Notice**. **Minutes are excluded**
— they already live as markdown under `meeting_minutes/` (Council) and
`planning_commission/`; duplicating them here would violate the "never touch existing
datasets" rule. (Park City's *Minutes* file also embeds the full packet, so it is bulky
and redundant with the Agenda Packet captured here.)

Each published file downloads from the collection-bound OData function
`Meetings/GetMeetingFileStream(fileId=<id>,plainText=false)` → `200 application/pdf`
(`plainText=true` → clean text). That fileId-keyed URL is the stable `source_url` on every
row. The null `agendaFile`/`minutesFile` scalar slots on the event are NOT the documents —
ignore them.

## Bodies harvested (3)

| categoryName (portal) | `body` in index | joins to |
|---|---|---|
| `City Council` (categoryId 26) | `Council` | `meeting_minutes/all_votes.csv` (body=Council) |
| `Planning Commission` | `PlanningCommission` | `planning_commission/all_votes.csv` |
| `Historic Preservation Board` | `HistoricPreservationBoard` | *(no vote dataset — kept for its agenda record)* |

Other CivicClerk categories exist (Planning Department Administrative Public Hearing,
Board of Adjustment, Recreation Advisory Board, Nonprofit Services Advisory Committee,
Appeal Panel, General) but carry no roll-call vote dataset in this repo and are **out of
scope** — a deliberate boundary, not a gap. HPB has no vote dataset either but is included
because it is a core land-use body whose agenda/packet record is the point of this dataset.

## Coverage (past events with documents), 2020-01 → 2026-07

Counts are of **past** events (dated on/before the 2026-07-05 retrieval). Future
placeholder events carry no files yet (expected, not a gap): Council 12, PC 9, HPB 5.

| Body | Past events | w/ Agenda | w/ Agenda Packet |
|------|------------:|----------:|-----------------:|
| Council                       | 249 | 242 | 239 |
| Planning Commission           | 223 | 163 | 163 |
| Historic Preservation Board   |  73 |  67 |  64 |

**Documents indexed (this dataset): 942** — **474 Agendas** (243 Council + 164 PC + 67 HPB)
+ **468 Agenda Packets** (240 Council + 164 PC + 64 HPB). (Agenda doc counts slightly
exceed agenda-event counts because one Council date, 2023-01-24, has two same-body events
that each publish an agenda.)

### Council-vs-PC-vs-HPB asymmetry (logged, not forced)
- **Council and HPB are near-complete** in CivicClerk: Council 97% of past events have an
  Agenda and 96% an Agenda Packet; HPB 92% / 88%.
- **Planning Commission is only ~73%** (163/223 for both Agenda and Packet). The shortfall
  is entirely **historical**: **47 of the 57 PC no-document dates fall in 2020–2022**.
  Park City migrated PC agenda/packet PDFs into CivicClerk reliably only from ~2023; older
  PC meetings survive in CivicClerk as **video archives** (they carry `hasMedia`) but with
  no agenda PDF attached. This is a source/portal limit, recorded here, not filled.

### Honest zeros — meetings that exist but publish no agenda PDF
**66 past date-groups** (5 Council, 57 PC, 4 HPB) have an event but no Agenda/Agenda Packet
file. **None are phantom events**: 61 carry meeting **video** (`hasMedia`) and the other 5
carry Minutes/Notice — they are real meetings whose agenda PDF was never posted to
CivicClerk (see the PC 2020–2022 pattern above). Recorded, not fabricated.

### Join coverage to the vote datasets — 100%
Every Council vote-date (**203/203**, 2020+) and every PC vote-date (**112/112**, 2020+)
has a matching agenda/packet document here. HPB has no vote dataset to join.

## Storage decision — HYBRID (Agendas stored, Packets index-only). Size math.

The two document classes are wildly different in size, so they get different treatment —
the same split used for Orem:

| Document | Files | Sized | Total | Avg | Max | Decision |
|----------|------:|------:|------:|----:|----:|----------|
| **Agenda**        | 474 | 474 (on disk) | **52.3 MB** | 110 KB | 729 KB | **STORED locally** |
| **Agenda Packet** | 468 | 468 (probed)  | **30,759 MB (30.1 GB)** | 65.7 MB | 449.9 MB | **INDEX-ONLY** |

- **Agendas are tiny born-digital outlines** (avg 110 KB; all 474 verified born-digital
  **text**, median 3,242 chars via `pdftotext`, zero scanned). At 52 MB the whole set fits
  comfortably under the ~400 MB local-store budget → **all 474 are stored** under
  `raw/<date>/`.
- **Agenda Packets are huge** image-heavy staff-report bundles (this is a resort city —
  plats, renderings, geotech). Full corpus ≈ **30.1 GB**, roughly **77× the ~400 MB
  budget**, so packets are **index-only**: each row has a live fileId-keyed `source_url`,
  `format=na`, `stored_locally=no`, empty `path`, and its **probed `size_mb`**. Nothing is
  silently capped or dropped — all 468 packets are enumerated and retrievable from their
  `source_url`; only the bytes are left on the portal. To materialize one later, GET its
  `source_url`; to bulk-fetch a subset, filter `index.csv` on `body`/`packet_kind`/`date`.

**All 468 packet sizes were probed** (streamed-GET `Content-Length`, body unread — the API
rejects HEAD with 405 and ignores Range). The packet-size totals above are therefore
complete for this window, **but the probe was point-in-time and not re-verified**; treat
`size_mb` as an as-of-2026-07-05 measurement, not a guarantee (packets can be re-published).

`raw/` contains the **474 Agenda PDFs** (`raw/<date>/<body>_e<eventid>_agenda.pdf`) plus
one consolidated **`raw/_fetch_log.jsonl`** — one line per download (`mode=download`, with
bytes/status) and one per packet size-probe (`mode=size_probe`, with `content_length`).
That log is the provenance record.

## Not built
- **No stored Agenda-Packet PDFs** (index-only; 30 GB over budget). `format=na` on those rows.
- **Minutes** — intentionally excluded (already in `meeting_minutes/` + `planning_commission/`;
  and Park City minutes embed the full packet).
- **Non-vote / out-of-scope boards** (Board of Adjustment, Planning-Admin hearings,
  Recreation Advisory Board, Nonprofit Services, Appeal Panel, General) — no vote dataset to join.

## Primary-document classes (doc_class rollout, 2026-07-16)

**Ruling: honest no — classes not separable for this portal.** Under the repo-wide
primary-documents rollout (`PRIMARY_DOCS_ROLLOUT.md`, triage 2026-07-16) Park City was
bucketed **B-no**. The **468 agenda_packets are INDEX-ONLY** (~30 GB, avg 66 MB, max
450 MB) resort image-heavy bundles whose **titles are meeting names** — one packet per
meeting, with no per-attachment rows or matter metadata to key a classifier on. The **474
stored thin agendas** are born-digital outlines that already carry `text/` sidecars serving
FTS (agenda outlines, not staff-analysis content). So the four attachment-borne classes —
`staff_report`, `member_memo`, `plan_amendment`, `development_agreement` — cannot be broken
out; nothing is fetched, classified, or section-cut this rollout and no `doc_class`/
`text_path` column is added.

**Separate known gap (unchanged here):** pre-~2023 Planning-Commission agenda/packet PDFs
were never migrated into CivicClerk (the PC-doc shortfall recorded above — 47 of 57 PC
no-document dates fall in 2020–2022). That is a source/portal limit, distinct from this
ruling. Class 3 (`general_plan`) is handled in `housing_plans/`.
