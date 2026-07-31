# Sandy City — agenda packets / staff reports: availability

**As-of:** 2026-07-05 (attachment catalog) / **2026-07-16** (primary-document text layer).
**Coverage window checked:** 2020-01-01 → 2026-12-31.
**Coverage window achieved:** 2020-01-02 → 2026-07-07 (full).
**Source:** Granicus **Legistar Web API** (`https://webapi.legistar.com/v1/sandyutah/`);
files hosted on `sandyutah.legistar1.com`. GET-only, browser UA, throttled (see `raw/_fetch_log.jsonl`).

## What a "packet" is here
Sandy runs Legistar, so a meeting packet decomposes into **separable parts**:
1. the **agenda PDF** (`EventAgendaFile`) — a born-digital text agenda listing every item; and
2. the **per-item matter attachments** (`matters/{id}/attachments`) — the actual staff
   reports, budget presentations, plats, maps, correspondence, and exhibits.
This dataset **stores the agenda PDFs** and **indexes every matter attachment** (live URL + size).

## Bodies enumerated (EventBodyId)
| Body | Id | Events 2020–26 | Agendas published | Agendas stored | Matter attachments (indexed) |
|------|----|----|----|----|----|
| City Council | 138 | 301 | 296 | 296 | 4,867 |
| Planning Commission | 140 | 158 | 157 | 157 | 1,527 |
| Board of Adjustment | 139 | 9 | 9 | 9 | 52 |
| Community Development | 173 | **0** | 0 | 0 | 0 |
| **Total** | | 468 | 462 | **462** | **6,446** |

- **No Council-vs-PC asymmetry in publishing:** both bodies expose full agenda PDFs *and*
  rich matter attachments through the API (Council 4,867 attachments, PC 1,527). This is the
  opposite of the Granicus/HTML cities where one body often publishes packets and the other not.
- **Board of Adjustment** is genuinely thin — only 9 meetings held 2020–2026 (it convenes rarely).
- **Community Development (173)** is a real Legistar body but has **zero events** in the window
  (nothing scheduled/published) — an honest empty, not an acquisition failure. CDBG (186) and
  Historic Preservation (187) bodies were not enumerated (out of the Council/PC/BoA/CD scope).
- 6 events (of 468) publish no `EventAgendaFile` (cancelled/placeholder meetings); their rows
  are absent from the agenda set but any attachments they reference are still indexed.

## Storage mode: agendas STORED, attachments INDEX-ONLY

**Decision: store the 462 agenda PDFs; index-only all 6,446 matter attachments.**

Size math (measured by HEAD Content-Length probe of every unique attachment URL, 2026-07-05):

| Bucket | Count | Size |
|--------|------|------|
| Agenda PDFs (stored) | 462 | **61.9 MB** on disk |
| Matter attachments — ALL | 6,446 | **14,884.7 MB (~14.9 GB)** |
| Matter attachments ≤4 MB (the "small" subset) | 5,446 | **4,080.6 MB (~4.1 GB)** |
| Matter attachments >4 MB | 661 | (largest single file 509 MB) |
| Matter attachments, size unknown (no Content-Length) | 339 | — |

The footprint ceiling for this dataset is **~400 MB**. Even the *small* (≤4 MB) attachment
subset is **4.08 GB — 10× over the ceiling** (and the full set is ~37×). Storing attachments
was therefore switched to **index-only**: every attachment is a catalog row with a live
`source_url`, its measured `size_mb`, `packet_kind`, `matter_id`, `format=na`, and
`stored_locally=no`. Nothing was silently capped or dropped — the entire attachment corpus is
enumerated and re-fetchable from the recorded URLs. Stored footprint on disk = **60 MB**.

The agenda PDFs are kept because they are uniformly small born-digital text (median ~130 KB),
they are the packet spine (they name every item + link the full packet), and 462×130 KB fits
comfortably under budget.

## Gaps / caveats
- **No dead agenda links.** 5 agenda GETs 404'd on the first pass (2020-09-01, 2020-10-06,
  2020-10-20, 2020-10-27, 2022-07-19) but all succeeded on retry — transient 404s under
  concurrent load, not missing files. All 462 published agendas are stored.
- **339 attachments have no `size_mb`** — the host returned no Content-Length on HEAD. They are
  still indexed with live URLs; size is simply unknown until fetched.
- **`meeting_type` is best-effort.** It is derived from the Legistar `EventComment` field
  (flags cancelled / work_session / special), defaulting to `regular`. Legistar does not tag
  work sessions structurally, so some work sessions whose agenda PDF says "Work Session" but
  whose EventComment is blank are labeled `regular`. Do not treat `meeting_type` as authoritative.
- **Attachments are keyed to the earliest meeting** whose agenda references their matter. A
  matter that recurs (e.g. an ordinance's 1st and 2nd reading) is indexed once, under its first
  appearance. `matter_id` lets you rejoin it to every event via the API.
- This dataset is **additive and read-only** — it touches no existing Sandy dataset.

## Primary-document text layer (2026-07-16 pilot)

889 of the 6,446 attachments were classified into four content-bearing `doc_class` values
(staff_report 739, member_memo 131, plan_amendment 19, development_agreement 0) and their
TEXT extracted to `text/attachments/` via a fetch → pdftotext/textutil → sha256 → discard-
binary pipeline (polite GET, ≥1 s/host, browser UA, provenance in `text/_fetch_log.jsonl`).
Outcome ledger:

| outcome | rows | note |
|---|---|---|
| ok (text on disk) | 863 | ~25.4 M chars — 767 born-digital (pdftotext/textutil, 24.0 M) + 96 Claude Vision (1.42 M; see below) |
| needs_ocr | 0 | was 96 scanned 2020–22-era packets w/ no text layer — **cleared 2026-07-17 by a Read-tool Claude Vision pass** (150 dpi over sha256-verified re-fetches; 96 docs / 980 pages; `extraction_method='claude_vision'`; imagery pages carry honest `[map/plat … — no text]` markers, source typos preserved verbatim) |
| 404 (dead URL) | 26 | Legistar attachment link rot as of 2026-07-16 — dated honest gaps (URLs in `text/_fetch_log.jsonl`) |

Honest-gap notes:
- **development_agreement is an EMPTY class for Sandy 2020–26**: no DA/MDA instruments are
  attached anywhere in the Legistar corpus (the only 2 matters mentioning development
  agreements are a 2020 City Attorney briefing and a 2026 council discussion — neither is an
  agreement). Not a classifier failure; verified by exhaustive title/matter sweeps.
- The 5,557 unclassified attachments (presentations, vicinity maps, plats/photos, minutes
  copies, resolutions, correspondence, eComment links, non-land-use staff reports) remain
  index-only by design — out of pilot scope, re-fetchable from `source_url`.
- Classifier precision/recall gates and boundary decisions: see `CLAUDE.md`.
