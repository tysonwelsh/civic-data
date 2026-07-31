# White City `pmn_backfill/` — what was checked, as-of 2026-07-13

Utah Public Notice (PMN, `utah.gov/pmn`) backfill for White City. GET-only, polite
(`scripts/polite_fetch.py`, browser UA, ≥1s/host). **Purely additive — no existing dataset
was modified.** See `coverage.md` for the full per-year tables and `CLAUDE.md` for method.

## PMN entity + body ids (resolved this run)
- **Entity 1325 = White City** (govType 3, Municipality). Its two public bodies:
  - **5805 = White City Council** (`/pmn/sitemap/publicbody/5805.html`) — 233 notices,
    2017–2026; 131 "Meeting Minutes" attachments.
  - **5879 = White City Planning Commission** — 176 notices, 2017–2026; 33 "Meeting
    Minutes" attachments across 28 notices. **This body was previously believed not to
    exist; it does.**
- Cross-checked, **excluded**: entity **840** = White City Water Improvement District
  (govType 5 — the recon's decoy special district) and entity **1345** = Greater SL
  Municipal Services District (its only bodies are a Board of Trustees + Town of
  Brighton items — no White-City PC body).
- Crawl method: cumulative `/pmn/list/notices.html?id=<body>&page=300` (one GET returns the
  body's full history, bypassing the 6-month list cap and the POST/CSRF search). Attachment
  type labels ("Meeting Minutes" vs "Public Information Handout"/"Other") parsed from the
  list HTML.

## What was recovered (31 documents → `index.csv`, raws in `raw/`)
- **Council (5):** 2019-11-14, 2022-03-03, 2022-08-18, 2023-10-05, 2023-11-02 — genuine
  gaps in the Streamline layer, born-digital narrative-tally minutes.
- **Planning Commission (22):** 2019-01-29 → 2025-05-20 — a **currently-empty core PC
  dataset**, now populated with real minutes (motion grammar, MSD Planning & Development
  Services letterhead). `body=PlanningCommission`.
- **General Plan Steering Committee (4):** 2021-02-09/02-23/03-09/03-23 — General-Plan
  drafting sub-body summaries. `body=GPSC`.

## What is NOT available (honest gaps → `unrecovered.csv`)
- **2017 council minutes (18 meetings)** and **2018-02-01, 2018-09-06** (20 total): PMN
  lists a "Meeting Minutes" attachment for each, but every file **404s** — the pre-~2019
  PMN blob purge (confirmed by probing the primary files AND their later "Public
  Information Handout" re-attachments; all 404). Streamline holds only the 2017 **agendas**.
  Unrecoverable from any checked source.
- **The bulk of PC meetings' minutes:** the PC met ~monthly for ~7 years but only 22
  meetings ever had a minutes document posted to PMN; the rest are agenda/packet-only
  ("Other" label) — a publishing gap, recorded honestly, never filled.
- No PC minutes on the Streamline `/meetings-archive` (agendas + packets only) or on the
  MSD site.

## Not modified (flagged for a future, separate remediation)
The repo's 2024-09-05 → 2025-01-02 council minutes (`format=ocr`) have **born-digital**
PMN copies (Public-Information-Handout label). A born-digital upgrade is possible but is
out of scope for this additive PMN-backfill dataset; not applied.

## Provenance
Every fetched byte is logged in `raw/_fetch_log.jsonl` (url, status, bytes, sha256,
retrieved_utc). Notice-list HTML, batch manifests, and discovery artifacts are retained in
`_disco/`. Text sidecars in `text/` (screened with `screen_corpus.py`; only the one
OCR'd/garbled file flagged, verified). Draft-vs-approved duplicate minutes (same meeting,
approved elsewhere) are retained in `raw/` as `*_draft.pdf` but indexed once per meeting.
