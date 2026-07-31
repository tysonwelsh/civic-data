# planning_commission — White City: RECOVERED FROM PMN BODY 5879 (2026-07-16)

**Verdict (SUPERSEDES the 2026-07-12 "honestly empty" verdict): White City's own
Planning Commission publishes no minutes on the city's Streamline site, but a real —
sporadic — PC minutes series exists on Utah Public Notice body 5879.** 22 minutes
documents (2019-01-29 → 2025-05-20) were recovered via `../pmn_backfill/` and promoted
into this dataset on 2026-07-16: **106 motions**, `provenance=pmn_minutes` on every row.
See `CLAUDE.md` in this directory for how to analyze them.

## What exists
- **Own Planning Commission — yes.** `whitecity.utah.gov/planning-commission`; cadence
  4th Thursday (schedule drifts — observed meetings fall on Tuesdays and Thursdays).
  **MSD-staffed**: minuted by Greater Salt Lake MSD Planning & Development Services
  ("MEETING MINUTE SUMMARY" letterhead, recorder Wendy Gurr) — the same document family
  as the Kearns PC.
- **Streamline site**: only agendas/packets/schedules + the adopted General Plan —
  NO minutes series (the 2026-07-12 finding stands for the city site).
- **PMN body 5879** (found by the 2026-07-13 `expand-city-sources` sweep; the original
  build missed it because PC notices sat next to the Water Improvement District decoy):
  176 notices 2017–2026, mostly agenda-only or cancelled; **22 carry a recoverable
  minutes attachment** — all promoted here.

## What was searched
1. **Streamline PC page + year pages + `/meetings-archive`** (2026-07-12, browser-UA
   GET): agendas/packets/schedules only, never minutes. The 2 candidate docs
   (`03-09-2017_pc_meeting.pdf`, `2019.11.04_pc_wcmtc.pdf`) failed the minutes-signature
   screen — they are an agenda and a packet (the 2019-11-04 *minutes* were later
   recovered from PMN).
2. **Utah PMN**: the original 2026-07-12 recon checked only council body 5805 and
   concluded no PC body existed — **that conclusion was wrong**; body 5879 was found
   2026-07-13 by sweeping ALL govTypes for entity 1325. Full recovery provenance:
   `../pmn_backfill/` (index rows, notice URLs, fetch log, discovery HTML).
3. **Greater Salt Lake MSD site** (`msd.utah.gov`): hosts no White City PC minutes
   series of its own.

## Honest residual gaps (recorded, never filled)
- `minutes_unrecovered.csv` — **29 PC meeting dates known/noticed but without minutes**:
  the 2017-03-09 Streamline agenda-only meeting + **28 dates (2017-04 → 2025-06) noticed
  on PMN body 5879 with an agenda but no minutes attachment ever posted**. The PC met
  roughly monthly; most months in 2024–2026 the notice carries a `*_Cancelled.pdf`
  (genuine cancellations, not gaps — the Copperton pattern).
- The recovered series is therefore **sporadic by source** — 22 minuted meetings across
  7 years is what the record holds, not a scraper miss.
- GPSC (General Plan Steering Committee) meetings noticed under body 5879 are a
  DIFFERENT sub-body (no roll-call motions) — 4 meeting reports live in
  `../pmn_backfill/` (`body=GPSC`), deliberately NOT counted as PC minutes.
