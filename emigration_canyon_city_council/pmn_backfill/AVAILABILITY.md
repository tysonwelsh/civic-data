# PMN backfill — availability (Emigration Canyon)

**As-of:** 2026-07-14. What was checked, what was recovered, what stays an honest gap.

## What exists here
- **1 recovered minutes doc:** Planning Commission **2025-11-13** (`raw/2025/…_1363983.pdf`
  + OCR sidecar `text/…`). Previously logged as unrecovered; the city posted the minutes
  late. Image-only scan → `format=scanned`, `extraction_method=ocr`.

## What was checked

### Bodies (complete)
- Confirmed the ONLY two Emigration Canyon PMN bodies: **5809** Council, **1562** PC
  (entity 1317). The *Emigration Improvement District* (entity 524) is a separate special
  district and was correctly excluded.

### MSD AgendaCenter (msd.utah.gov) — the named 2017-backfill avenue: EMPTY of EC minutes
- Enumerated the entire CivicPlus AgendaCenter (all 189 meeting-ids) + the DocumentCenter
  Emigration Canyon folder. It carries the **MSD Board of Trustees** and a few other
  townships (Magna/White City/Kearns/Copperton) — **zero Emigration Canyon Council or
  Planning Commission meeting minutes.** So the documented backfill avenue yields nothing
  for the purged 2017 gap. Detail + the enumeration table in `coverage.md` §(a).

### PMN sweep (both bodies, full history)
- 211 council + 268 PC notices swept; the audited datasets are a **superset by
  meeting-date** of every live PMN minutes doc. Only the 2025-11-13 PC minutes had been
  posted after the original harvest → recovered here. 58 other non-repo live minutes
  file-ids are re-uploads / draft-vs-approved / attachment-packet variants of dates the
  repo already holds (not gaps). Detail in `coverage.md` §(b).

## Honest gaps — NOT filled (verified genuine, do not fabricate)

1. **Purged pre-2018-10 minutes** (PMN file store rot; boundary file-id ≈ 450000). Every
   probed 2017 + early-2018 council/PC file-id returns a 315-byte 404; the repo floor
   (459655 = 2018-10-25) downloads. Recovered coverage begins **2018-10-25** (council) /
   **2018-11-15** (PC). Council: 1 purged date (2017-01-04) + scattered; PC: 14 purged
   2017 dates + scattered 2018-19 — several 2017 PC meetings were CANCELLED (no minutes
   ever existed). These remain in the two `minutes_unrecovered.csv` files. **No MSD mirror
   exists to backfill them** (see above).

2. **Later meetings whose minutes were never posted / not yet approved** — the remaining
   `minutes_unrecovered.csv` rows (e.g. council 2024-08-27, 2025-02-25…; PC 2019–2023
   "no approved-minutes doc recovered", 2026-04-09/04-15 pending). Re-checked against the
   live PMN attachment set: no minutes doc is currently published for them (2026-04 PC
   minutes are simply not yet posted). Not recoverable now; a future `refresh-city` run
   may pick up late posts (as 2025-11-13 was picked up here).

3. **Image-only audited scans with no born-digital copy** — council 2024-02-22 (Regular,
   1163111) and 2025-01-28 (1254241) yielded 0 motions; **no born-digital replacement
   exists on PMN or MSD** (coverage.md §(c)). An upstream publication limit; cataloged as
   permanent OCR-only, not an extraction defect.

## Scope note
This dataset is deliberately kept SEPARATE from the audited `meeting_minutes/` +
`planning_commission/` layers. At build time (2026-07-14) nothing outside this dataset was
modified. **Update 2026-07-16:** the 2025-11-13 PC recovery was subsequently PROMOTED into
`planning_commission/` (index `format=ocr`, `provenance=pmn_minutes`, +2 motions,
unrecovered row dropped, derived layers rebuilt) — see `CLAUDE.md` §Linkage. This dataset
itself is unchanged and retains the recovery record.
