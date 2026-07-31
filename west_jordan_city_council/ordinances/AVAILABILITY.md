# ordinances/ — availability & gaps

**As-of 2026-07-03; backfill 2026-07-19.** What was checked, what exists, what does not.

**2026-07-19 backfill:** the 8 owed ordinances 26-26..33 (adopted/postponed at the 2026-06-09 and
2026-06-23 council meetings, now in the extended vote record) were added. 6 signed PDFs were
retrieved from the Recorder "Adopted Ordinances" page (26-26 compensation, 26-27 FY26 budget
amendment, 26-28 Diaz Lot rezone, 26-31 7800 South Commercial FLUM+rezone, 26-32 streetlight
standards, 26-33 Title 1/2 advice-and-consent) — all born-digital, each self-citing its number and
adoption date → `high`. 26-29 / 26-30 (Sugar Factory on Town Creek) were **postponed** on 2026-06-09
to a date uncertain, so no adopted ordinance was recorded and none is posted — they stay
`within_source` / `tabled`.

## Summary

| | count |
|---|---|
| Ordinances in index (2020–2026) | 293 |
| — from council motions only (`within_source`, no PDF) | 226 |
| — with independent signed PDF cross-matched to a motion (`high`) | 64 |
| — signed PDF exists but NOT in any motion (`none`, discrepancy) | 3 |
| Signed PDFs retrieved (raw/, ~48 MB) | 67 |
| Zoning/land-use ordinances in index | 130 |
| Zoning ordinances backed by a retrieved PDF | 63 |

## What exists and was retrieved

- **Full number→date→subject→motion index for every ordinance cited in the council vote
  record, 2020–2026** (290 ordinances), derived from `meeting_minutes/all_votes.csv`. This is
  complete for the vote-record window (now extended through 2026-06-23) and is the authoritative
  backbone.
- **67 recorder-signed ordinance PDFs**, concentrated **2021–2026**
  (2021×4, 2022×12, 2023×6, 2024×14, 2025×25, **2026×6**). The 2026 six (from the 2026-07-19
  backfill) are the first non-zoning signed PDFs in the set: 26-28 and 26-31 are zoning
  (rezone / FLUM+rezone), while 26-26 (compensation), 26-27 (budget amendment), 26-32
  (streetlight standards) and 26-33 (Title 1/2 code amendment) are non-zoning — so "signed PDFs
  retrieved" (67) and "zoning ordinances backed by a PDF" (63) now diverge. These are the actual adopted text (rezone
  ordinances, GPLUM/FLUM map amendments, Title 13 code-text amendments, MDAs, annexations).

## What is NOT available (verified gaps)

### 1. 2020 signed ordinance PDFs — entirely unavailable (17 zoning ordinances)
The 2020 ordinances predate the city's WordPress migration and live on a legacy hashed asset
host (`assets.westjordan.utah.gov/ugd/c1b6d4_<hash>.pdf`) that is **not enumerable** — a signed
PDF only surfaces if a search engine indexed its exact hash. Multiple targeted searches returned
**zero** 2020 signed PDFs. These 17 remain `within_source` (known from the motion, no adopted
text): 20-12, 20-13, 20-17, 20-18, 20-21, 20-24, 20-29, 20-30, 20-32, 20-37, 20-39, 20-41,
20-42, 20-45, 20-46, 20-48, 20-50. **Recovery path:** Utah PMN back-catalog (SOURCE 4) or a
GRAMA request to the City Recorder; the legacy hashes are otherwise unrecoverable.

### 2. Many 2021–2023 ordinances have no web-posted signed PDF
Zoning ordinances known from motions but with **no retrievable signed PDF** by year:
2021×17, 2022×8, 2023×7, 2024×4, 2025×2 (plus all of 2026 by scope). The city reliably posts
signed PDFs for **rezones / map amendments / MDAs / annexations** but frequently does **not**
post a standalone signed PDF for pure **Title 13 code-text amendments** (those appear only inside
the PrimeGov "Complete Packet"). Examples confirmed to exist but unposted: the Wood Ranch suite
(21-42/43/46/47), Welby West (22-26, only the agenda packet is online), Mountain America (22-31,
only the PC staff report is online), Next Level Homes (23-07), Cottages at Parker Place
(24-06/07). These stay `within_source`.

### 3. Cross-source discrepancy — signed ordinances NOT in the vote record (3)
Real, recorder-signed adopted ordinances whose numbers do **not** appear in any
`all_votes.csv` motion:

| ordinance | adopted | subject | note |
|---|---|---|---|
| 22-08 | 2022-04-13 | Hidden Cove Rezone | signed PDF retrieved; no motion cites 22-08 |
| 23-08 | 2023-05-02 | Jordan River Heights Rezone | PDF: "presented to the Mayor by the City Council on May 2, 2023"; no motion cites 23-08 |
| 24-18 | 2024-04-24 | Taylor Farms Rezone | signed PDF retrieved; no motion cites 24-18 |

Likely a minutes-extraction gap (adopted on a consent block without the number in the motion
string) rather than an unadopted ordinance. **Flagged, not fixed** — the existing
`meeting_minutes/` vote layer was not modified (additive-only rule). Worth a look when that layer
is next audited/refreshed.

## Hosts checked (see CLAUDE.md)

- **Municode** `library.municode.com/ut/west_jordan` — current consolidated code only (Angular
  SPA); no per-ordinance adoption archive. Not a per-ordinance source.
- **City Recorder Adopted-Ordinances page** — best for 2024–2026; lazy-loaded; WP media REST API
  locked (returns 0) so PDFs found by web search only.
- **PrimeGov** — no standalone ordinance document type; ordinance text is buried in Complete
  Packets.
- **Legacy `assets.westjordan.utah.gov/ugd/…`** — pre-2022 signed PDFs, hashed, not enumerable.

## unrecovered items
Machine-readable list of zoning ordinances known from motions but with no retrieved adopted text:
`index.csv` rows where `zoning=Y AND path is empty` (67 rows; 2020×17, 2021×17, 2022×8, 2023×7,
2024×4, 2025×2, 2026×12). The 2026-07-19 backfill added 26-28 and 26-31 with PDFs (so they are
NOT in this list) and 26-29 / 26-30 without adopted text (postponed — the only new additions to it).
